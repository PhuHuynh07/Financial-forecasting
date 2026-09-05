"""
Module: ai_agent.py
Bộ não AI tài chính đa tầng (Vision + Agentic Function Calling + Chain of Thought Reasoning + Token Optimization).
Hỗ trợ chính thức:
1. Google Gemini API (Gemini 3.6 Flash / 3.7 Flash / 3.5 Flash-Lite / 3.1 Pro) qua google-genai SDK.
2. OpenAI API (GPT-4o / GPT-4o-mini).
3. Chế độ Demo / Mô phỏng (Hoạt động 100% không cần API Key để người dùng thử nghiệm ngay).
"""

import os
import io
import json
import base64
import time
from typing import Dict, Any, Tuple, Optional, Callable
from PIL import Image
from dotenv import load_dotenv

from market_data import get_stock_market_data, format_market_summary_for_ai
from token_tracker import record_token_usage

load_dotenv(override=True)


def optimize_image_for_vision(
    image: Image.Image,
    max_dimension: int = 1024,
    quality: int = 85
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Kỹ thuật Token Optimization:
    Chuẩn hóa và nén ảnh biểu đồ bằng Pillow để giữ độ sắc nét của nến
    nhưng giảm thiểu đáng kể số lượng vision tokens (tối ưu 50-70% chi phí).
    """
    orig_w, orig_h = image.size
    
    # Chuyển đổi RGBA sang RGB nếu cần
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
        
    # Giảm kích thước tỉ lệ nếu vượt quá max_dimension
    if max(orig_w, orig_h) > max_dimension:
        if orig_w > orig_h:
            new_w = max_dimension
            new_h = int(orig_h * (max_dimension / orig_w))
        else:
            new_h = max_dimension
            new_w = int(orig_w * (max_dimension / orig_h))
        resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    else:
        resized_img = image
        new_w, new_h = orig_w, orig_h

    # Xuất ra JPEG buffer với quality tối ưu
    buf = io.BytesIO()
    resized_img.save(buf, format="JPEG", quality=quality, optimize=True)
    buf.seek(0)
    optimized_pil = Image.open(buf)
    
    meta = {
        "original_size": (orig_w, orig_h),
        "optimized_size": (new_w, new_h),
        "file_size_kb": round(buf.getbuffer().nbytes / 1024, 2)
    }
    return optimized_pil, meta


SYSTEM_PROMPT = """Bạn là Chuyên gia Cao cấp Phân tích Kỹ thuật & Định giá Tài chính (Chief Technical Market Analyst).
Nhiệm vụ của bạn là nhận diện các mô hình giá (Price Action / Chart Patterns) từ ảnh chụp biểu đồ nến của người dùng, sử dụng Tool được cung cấp để lấy dữ liệu giá thực tế hiện tại, và đưa ra khuyến nghị đầu tư chính xác với tư duy logic đa tầng.

QUY TẮC PHÂN TÍCH & TRÌNH BÀY BẮT BUỘC:
1. MÔ HÌNH NẾN: Phải chỉ rõ tên mô hình chính xác (Head & Shoulders, Bullish/Bearish Engulfing, Double Top/Bottom, Cup & Handle, Ascending Triangle, v.v.).
2. GỌI TOOL AGENT: Sau khi nhận diện mã cổ phiếu từ ảnh (hoặc từ mô tả), BẮT BUỘC gọi tool `fetch_realtime_market_data` để lấy dữ liệu thực tế nhằm đối chiếu với ảnh chụp.
3. QUY TRÌNH TƯ DUY (Chain of Thought): Bạn PHẢI giải thích cặn kẽ logic từng bước: tại sao nhận diện đó là mô hình này (hình học đỉnh/đáy, tỉ lệ nến, khối lượng volume, đường viền cổ neckline).
4. KHUYẾN NGHỊ: Cung cấp kế hoạch hành động rõ ràng: Hành động (MUA MẠNH / MUA / QUAN SÁT / BÁN / CẮT LỖ), Điểm vào (Entry), Điểm chốt lời (TP1, TP2), Điểm cắt lỗ (SL), Tỉ lệ Lợi nhuận/Rủi ro (R:R).
5. Trả lời bằng Tiếng Việt chuyên nghiệp, súc tích, cấu trúc Markdown rõ ràng."""


# ------------------- GOOGLE GEMINI PIPELINE -------------------

def execute_gemini_pipeline(
    image: Image.Image,
    user_ticker: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    alpha_vantage_key: Optional[str] = None,
    model_name: str = "gemini-3.6-flash",
    status_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """Thực thi quy trình Agentic sử dụng Google GenAI SDK (Gemini 3.6 Flash / 3.7 Flash)."""
    from google import genai
    from google.genai import types

    if not gemini_api_key or gemini_api_key.strip() == "":
        gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")

    if not gemini_api_key or gemini_api_key.strip() == "":
        raise ValueError("Chưa nhập Google Gemini API Key! Vui lòng nhập Key tại thanh Sidebar hoặc bật Chế độ Demo.")

    client = genai.Client(api_key=gemini_api_key.strip())

    # 1. Tối ưu ảnh và chuyển sang bytes
    if status_callback:
        status_callback("Đang nén & tối ưu hóa ảnh biểu đồ bằng Pillow...")
    optimized_img, img_meta = optimize_image_for_vision(image, max_dimension=1024)

    buf = io.BytesIO()
    optimized_img.save(buf, format="JPEG", quality=85)
    img_part = types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")

    # State tracking cho tool execution
    tool_state = {
        "called": False,
        "ticker": user_ticker.strip().upper() if user_ticker else "UNKNOWN",
        "market_data": None
    }

    # Định nghĩa Tool Python cho Google Gemini Function Calling
    def fetch_realtime_market_data(ticker_symbol: str) -> str:
        """Lấy dữ liệu giá thời gian thực, khối lượng giao dịch, RSI(14), MA20, MA50, MA200 và vùng hỗ trợ/kháng cự của một mã cổ phiếu từ thị trường thực tế (Alpha Vantage / Yahoo Finance).
        
        Args:
            ticker_symbol: Mã cổ phiếu cần tra cứu (ví dụ: AAPL, NVDA, TSLA, MSFT, BTC-USD, SPY).
        """
        sym = ticker_symbol.strip().upper()
        tool_state["called"] = True
        tool_state["ticker"] = sym
        if status_callback:
            status_callback(f"Agent đang gọi Tool: Lấy dữ liệu thị trường thực tế cho {sym}...")
        
        m_data = get_stock_market_data(sym, alpha_vantage_key=alpha_vantage_key)
        tool_state["market_data"] = m_data
        return format_market_summary_for_ai(m_data)

    # 2. Xây dựng prompt
    user_prompt = "Hãy phân tích biểu đồ nến đính kèm."
    if user_ticker and user_ticker.strip():
        user_prompt += f" Mã cổ phiếu được chỉ định: {user_ticker.strip().upper()}."
    else:
        user_prompt += " Hãy trích xuất mã cổ phiếu (ticker) từ biểu đồ nếu có, hoặc suy đoán/chọn mã phù hợp nhất để gọi tool lấy dữ liệu thực tế."

    user_prompt += (
        "\n1. Nhận diện các mô hình giá (Chart Patterns) và xu hướng chính."
        "\n2. Hãy gọi tool `fetch_realtime_market_data` với mã cổ phiếu tìm thấy."
        "\n3. So sánh dữ liệu trên biểu đồ ảnh với dữ liệu thị trường thực tế."
        "\n4. Trình bày chi tiết [QUY TRÌNH TƯ DUY (Chain of Thought)] giải thích tại sao bạn nhận định như vậy trước khi đưa ra khuyến nghị."
    )

    if status_callback:
        status_callback(f"Đang gửi dữ liệu đến {model_name} (Vision + Auto Function Calling)...")

    config = types.GenerateContentConfig(
        tools=[fetch_realtime_market_data],
        system_instruction=SYSTEM_PROMPT,
        temperature=0.2
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[img_part, user_prompt],
            config=config
        )
    except Exception as e:
        err_str = str(e)
        if ("404" in err_str or "503" in err_str or "overloaded" in err_str.lower() or "no longer available" in err_str.lower()) and model_name != "gemini-3.6-flash":
            if status_callback:
                status_callback(f"Mô hình {model_name} không khả dụng, tự động chuyển sang gemini-3.6-flash...")
            model_name = "gemini-3.6-flash"
            response = client.models.generate_content(
                model=model_name,
                contents=[img_part, user_prompt],
                config=config
            )
        else:
            raise e

    final_text = response.text or ""

    prompt_tokens = 0
    completion_tokens = 0
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        prompt_tokens = response.usage_metadata.prompt_token_count or 0
        completion_tokens = response.usage_metadata.candidates_token_count or 0

    detected_sym = tool_state["ticker"]
    if detected_sym == "UNKNOWN" and user_ticker:
        detected_sym = user_ticker.strip().upper()

    market_data_result = tool_state["market_data"]
    if market_data_result is None and detected_sym != "UNKNOWN":
        market_data_result = get_stock_market_data(detected_sym, alpha_vantage_key=alpha_vantage_key)

    token_record = record_token_usage(
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
        model=model_name,
        task_name=f"Gemini Vision Analysis ({detected_sym})"
    )

    return {
        "analysis_report": final_text,
        "detected_symbol": detected_sym,
        "market_data": market_data_result,
        "image_metadata": img_meta,
        "provider": f"Google Gemini ({model_name})",
        "token_usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": token_record["cost_usd"],
            "cost_vnd": token_record["cost_vnd"]
        }
    }


# ------------------- OPENAI PIPELINE -------------------

OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_realtime_market_data",
            "description": "Lấy dữ liệu giá thời gian thực, khối lượng giao dịch, RSI(14), MA20, MA50, MA200 và vùng hỗ trợ/kháng cự của một mã cổ phiếu từ thị trường thực tế (Alpha Vantage / Yahoo Finance).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker_symbol": {
                        "type": "string",
                        "description": "Mã cổ phiếu cần tra cứu (ví dụ: AAPL, NVDA, TSLA, MSFT, BTC-USD, SPY)."
                    }
                },
                "required": ["ticker_symbol"]
            }
        }
    }
]

def execute_openai_pipeline(
    image: Image.Image,
    user_ticker: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    alpha_vantage_key: Optional[str] = None,
    model_name: str = "gpt-4o",
    vision_detail: str = "auto",
    status_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """Thực thi quy trình Agentic sử dụng OpenAI SDK."""
    from openai import OpenAI

    if not openai_api_key or openai_api_key.strip() == "":
        openai_api_key = os.getenv("OPENAI_API_KEY", "")

    if not openai_api_key or openai_api_key.strip() == "":
        raise ValueError("Chưa cấu hình OpenAI API Key! Vui lòng nhập API Key trên Sidebar hoặc bật Chế độ Demo.")

    client = OpenAI(api_key=openai_api_key.strip())

    total_prompt_tokens = 0
    total_completion_tokens = 0

    if status_callback:
        status_callback("Đang tối ưu hóa hình ảnh & chuyển đổi Base64...")
    optimized_img, img_meta = optimize_image_for_vision(image, max_dimension=1024)

    buf = io.BytesIO()
    optimized_img.save(buf, format="JPEG", quality=85)
    base64_data = base64.b64encode(buf.getvalue()).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{base64_data}"

    user_prompt = "Hãy phân tích biểu đồ nến đính kèm."
    if user_ticker and user_ticker.strip():
        user_prompt += f" Mã cổ phiếu được chỉ định: {user_ticker.strip().upper()}."
    else:
        user_prompt += " Hãy trích xuất mã cổ phiếu (ticker) từ biểu đồ nếu có, hoặc suy đoán/chọn mã phù hợp nhất để gọi tool lấy dữ liệu thực tế."

    user_prompt += (
        "\n1. Nhận diện các mô hình giá (Chart Patterns) và xu hướng chính."
        "\n2. Hãy gọi tool `fetch_realtime_market_data` với mã cổ phiếu tìm thấy."
        "\n3. So sánh dữ liệu trên biểu đồ ảnh với dữ liệu thị trường thực tế."
        "\n4. Trình bày chi tiết [QUY TRÌNH TƯ DUY (Chain of Thought)] giải thích tại sao bạn nhận định như vậy trước khi đưa ra khuyến nghị."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": data_uri, "detail": vision_detail}
                }
            ]
        }
    ]

    if status_callback:
        status_callback(f"Đang phân tích hình ảnh bằng {model_name}...")

    response1 = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=OPENAI_TOOLS,
        tool_choice="auto",
        temperature=0.2
    )

    if response1.usage:
        total_prompt_tokens += response1.usage.prompt_tokens
        total_completion_tokens += response1.usage.completion_tokens

    response_msg1 = response1.choices[0].message
    tool_calls = response_msg1.tool_calls

    tool_results_data = None
    detected_symbol = user_ticker.strip().upper() if (user_ticker and user_ticker.strip()) else "UNKNOWN"

    if tool_calls:
        messages.append(response_msg1)
        for tool_call in tool_calls:
            if tool_call.function.name == "fetch_realtime_market_data":
                func_args = json.loads(tool_call.function.arguments or "{}")
                target_symbol = func_args.get("ticker_symbol", user_ticker or "AAPL").strip().upper()
                detected_symbol = target_symbol
                
                if status_callback:
                    status_callback(f"Agent đang gọi Tool: Lấy dữ liệu thị trường cho {target_symbol}...")
                
                m_data = get_stock_market_data(target_symbol, alpha_vantage_key=alpha_vantage_key)
                tool_results_data = m_data
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": format_market_summary_for_ai(m_data)
                })

        if status_callback:
            status_callback("Đang tổng hợp suy luận Chuỗi Tư duy (CoT)...")

        response2 = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.3
        )
        if response2.usage:
            total_prompt_tokens += response2.usage.prompt_tokens
            total_completion_tokens += response2.usage.completion_tokens
            
        final_content = response2.choices[0].message.content or ""
    else:
        if detected_symbol != "UNKNOWN":
            tool_results_data = get_stock_market_data(detected_symbol, alpha_vantage_key=alpha_vantage_key)
        final_content = response_msg1.content or ""

    token_record = record_token_usage(
        input_tokens=total_prompt_tokens,
        output_tokens=total_completion_tokens,
        model=model_name,
        task_name=f"OpenAI Vision Analysis ({detected_symbol})"
    )

    return {
        "analysis_report": final_content,
        "detected_symbol": detected_symbol,
        "market_data": tool_results_data,
        "image_metadata": img_meta,
        "provider": f"OpenAI ({model_name})",
        "token_usage": {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "cost_usd": token_record["cost_usd"],
            "cost_vnd": token_record["cost_vnd"]
        }
    }


# ------------------- DEMO / SIMULATION PIPELINE (NO API KEY NEEDED) -------------------

def execute_demo_pipeline(
    image: Image.Image,
    user_ticker: Optional[str] = "AAPL",
    status_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """Chế độ Demo/Mô phỏng: Cho phép chạy thử nghiệm ngay lập tức lấy giá live thật mà không cần API Key."""
    ticker = (user_ticker.strip().upper() if user_ticker and user_ticker.strip() else "AAPL")
    
    if status_callback:
        status_callback("Đang phân tích cấu trúc nến trong chế độ Demo Simulation...")
        time.sleep(0.6)
        status_callback(f"Agent đang kết nối dữ liệu thị trường thực tế cho {ticker}...")
        
    mdata = get_stock_market_data(ticker)
    curr_p = mdata.get("current_price", 185.0)
    tech = mdata.get("technical_indicators", {})
    rsi = tech.get("rsi_14", 58.4)
    ma20 = tech.get("sma_20", curr_p * 0.98)
    ma50 = tech.get("sma_50", curr_p * 0.95)

    if status_callback:
        status_callback("Đang tạo báo cáo suy luận Chuỗi Tư duy (Chain of Thought)...")
        time.sleep(0.5)

    report = f"""### 🧠 QUY TRÌNH TƯ DUY (Chain of Thought — Step by Step Reasoning)

1. **Khảo sát Hình học Nến & Đỉnh Đáy**:
   - Biểu đồ thể hiện rõ cấu trúc tạo đáy/đỉnh liên hoàn với các ngưỡng hỗ trợ quan trọng.
   - Nhận diện sự xuất hiện của mô hình giá có xác suất cao với lực cầu hấp thụ mạnh tại vùng giá hỗ trợ.

2. **Xác nhận Khối lượng Giao dịch (Volume Analysis)**:
   - Các phiên tăng điểm ghi nhận Volume đột biến tăng so với mức trung bình 20 phiên.
   - Phe Mua (Bulls) đang kiểm soát thế trận tại các nhịp điều chỉnh ngắn hạn.

3. **Đối chiếu Dữ liệu Thị trường Thời gian Thực**:
   - Giá hiện tại của **{ticker}** là **${curr_p}**, đang nằm trên đường trung bình MA20 (${ma20}) và MA50 (${ma50}).
   - Chỉ báo **RSI (14)** đang ở mức **{rsi}**, phản ánh động lượng tăng trưởng lành mạnh, chưa rơi vào vùng quá mua nguy hiểm.

4. **Đánh giá Tỷ lệ Lợi nhuận / Rủi ro (Risk : Reward)**:
   - Khoảng cách đến ngưỡng kháng cự gần nhất đem lại tỷ lệ R:R đạt **~2.8:1**, thỏa mãn tiêu chuẩn quản trị rủi ro chuyên nghiệp.

---

### 📊 NHẬN DIỆN MÔ HÌNH GIÁ & XU HƯỚNG
- **Mô hình xác định:** Mô hình Đảo chiều Kỹ thuật (Price Action Reversal Confirmation)
- **Độ tin cậy (Confidence Score):** **92%**
- **Xu hướng chính:** **Tăng trưởng ngắn hạn (Bullish Momentum)**
- **Vùng Kháng cự trọng yếu:** ~ **${curr_p * 1.08:.2f}**
- **Vùng Hỗ trợ then chốt:** ~ **${curr_p * 0.95:.2f}**

---

### 🎯 KHUYẾN NGHỊ GIAO DỊCH & QUẢN TRỊ RỦI RO

| Thông số Chiến lược | Giá trị Đề xuất | Ghi chú Phân tích |
| :--- | :--- | :--- |
| **Khuyến nghị Hành động** | 🟢 **MUA (BUY)** | Tín hiệu xác nhận đồng thuận giữa nến và Volume |
| **Vùng Mua (Entry Zone)** | **${curr_p * 0.99:.2f} - ${curr_p:.2f}** | Mở vị thế tích lũy quanh vùng giá hiện tại |
| **Mục tiêu 1 (TP1)** | **${curr_p * 1.05:.2f}** (+5.0%) | Chốt lời từng phần tại đỉnh ngắn hạn |
| **Mục tiêu 2 (TP2)** | **${curr_p * 1.10:.2f}** (+10.0%) | Kỳ vọng sóng mở rộng theo Fibonacci |
| **Cắt lỗ (Stop Loss - SL)** | **${curr_p * 0.96:.2f}** (-4.0%) | Vi phạm đáy nền giá gần nhất |
| **Tỷ lệ R : R** | **2.5 : 1** | Rủi ro thấp, biên lợi nhuận kỳ vọng cao |
"""

    token_record = record_token_usage(
        input_tokens=1420,
        output_tokens=680,
        model="gemini-3.6-flash",
        task_name=f"Demo Simulation ({ticker})"
    )

    return {
        "analysis_report": report,
        "detected_symbol": ticker,
        "market_data": mdata,
        "image_metadata": {"original_size": image.size, "optimized_size": (1024, 576), "file_size_kb": 120.5},
        "provider": "Demo Simulation Engine (No Key Required)",
        "token_usage": {
            "prompt_tokens": 1420,
            "completion_tokens": 680,
            "total_tokens": 2100,
            "cost_usd": token_record["cost_usd"],
            "cost_vnd": token_record["cost_vnd"]
        }
    }


# ------------------- UNIFIED DISPATCHER -------------------

def execute_financial_agent_pipeline(
    image: Image.Image,
    provider: str = "Google Gemini",
    user_ticker: Optional[str] = None,
    api_key: Optional[str] = None,
    alpha_vantage_key: Optional[str] = None,
    model_name: str = "gemini-3.6-flash",
    vision_detail: str = "auto",
    status_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """Hàm điều phối: Tự động phân luồng Gemini, OpenAI hoặc Demo Mode."""
    if "Demo" in provider or provider == "demo":
        return execute_demo_pipeline(
            image=image,
            user_ticker=user_ticker,
            status_callback=status_callback
        )
    
    # Tự động nhận diện key nếu người dùng dán key
    if api_key:
        clean_key = api_key.strip()
        if clean_key.startswith("AIzaSy"):
            provider = "Google Gemini"
        elif clean_key.startswith("sk-"):
            provider = "OpenAI"

    if "Gemini" in provider or "gemini" in model_name.lower():
        return execute_gemini_pipeline(
            image=image,
            user_ticker=user_ticker,
            gemini_api_key=api_key,
            alpha_vantage_key=alpha_vantage_key,
            model_name=model_name,
            status_callback=status_callback
        )
    else:
        return execute_openai_pipeline(
            image=image,
            user_ticker=user_ticker,
            openai_api_key=api_key,
            alpha_vantage_key=alpha_vantage_key,
            model_name=model_name,
            vision_detail=vision_detail,
            status_callback=status_callback
        )
