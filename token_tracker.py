"""
Module: token_tracker.py
Quản lý, đếm và hiển thị thời gian thực lượng Token (Prompt/Input, Completion/Output, Tổng)
và ước tính chi phí sử dụng API Google Gemini & OpenAI trên giao diện Streamlit Sidebar.
"""

from typing import Dict, Any, List
import streamlit as st

# Bảng giá chuẩn cập nhật (per 1M tokens)
MODEL_PRICING = {
    # Google Gemini Models
    "gemini-3.6-flash": {
        "input_per_1m": 0.10,    # $0.10 / 1M input tokens
        "output_per_1m": 0.40,   # $0.40 / 1M output tokens
        "provider": "Google Gemini",
        "name": "Gemini 3.6 Flash (Khuyên dùng - Nhanh & Ổn định)"
    },
    "gemini-3.7-flash": {
        "input_per_1m": 0.10,
        "output_per_1m": 0.40,
        "provider": "Google Gemini",
        "name": "Gemini 3.7 Flash (Hybrid Reasoning & Multimodal)"
    },
    "gemini-3.5-flash-lite": {
        "input_per_1m": 0.05,
        "output_per_1m": 0.20,
        "provider": "Google Gemini",
        "name": "Gemini 3.5 Flash-Lite (Siêu Tiết kiệm)"
    },
    "gemini-3.1-pro-preview": {
        "input_per_1m": 1.25,
        "output_per_1m": 5.00,
        "provider": "Google Gemini",
        "name": "Gemini 3.1 Pro (Deep Technical Reasoning)"
    },
    # OpenAI Models
    "gpt-4o": {
        "input_per_1m": 2.50,
        "output_per_1m": 10.00,
        "provider": "OpenAI",
        "name": "GPT-4o (Omni Flagship)"
    },
    "gpt-4o-mini": {
        "input_per_1m": 0.15,
        "output_per_1m": 0.60,
        "provider": "OpenAI",
        "name": "GPT-4o Mini"
    }
}

USD_TO_VND = 25400  # Tỷ giá ước tính USD/VND


def init_token_state():
    """Khởi tạo state quản lý token trong streamlit session nếu chưa có."""
    if "token_stats" not in st.session_state:
        st.session_state.token_stats = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "calls_count": 0,
            "history": []  # List of {call_index, model, input, output, total, cost, task}
        }


def record_token_usage(
    input_tokens: int,
    output_tokens: int,
    model: str = "gemini-3.6-flash",
    task_name: str = "Phân tích Kỹ thuật + Live Data"
) -> Dict[str, Any]:
    """Ghi nhận lượng token tiêu thụ từ một lần gọi API."""
    init_token_state()
    
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["gemini-3.6-flash"])
    cost_input = (input_tokens / 1_000_000) * pricing["input_per_1m"]
    cost_output = (output_tokens / 1_000_000) * pricing["output_per_1m"]
    total_cost = cost_input + cost_output
    total_tokens = input_tokens + output_tokens

    # Cập nhật tổng tích lũy
    st.session_state.token_stats["total_input_tokens"] += input_tokens
    st.session_state.token_stats["total_output_tokens"] += output_tokens
    st.session_state.token_stats["total_tokens"] += total_tokens
    st.session_state.token_stats["total_cost_usd"] += total_cost
    st.session_state.token_stats["calls_count"] += 1

    entry = {
        "call_index": st.session_state.token_stats["calls_count"],
        "task": task_name,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cost_usd": total_cost,
        "cost_vnd": total_cost * USD_TO_VND
    }
    st.session_state.token_stats["history"].append(entry)
    return entry


def reset_token_stats():
    """Đặt lại bộ đếm token về 0."""
    st.session_state.token_stats = {
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_tokens": 0,
        "total_cost_usd": 0.0,
        "calls_count": 0,
        "history": []
    }


def render_sidebar_token_tracker(current_model: str = "gemini-3.6-flash"):
    """Hiển thị bảng điều khiển Token Real-time trên Sidebar của Streamlit."""
    init_token_state()
    stats = st.session_state.token_stats
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ Quản lý Token & Chi phí AI")

    # Metrics hiển thị lớn
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric(
            label="📥 Input Tokens",
            value=f"{stats['total_input_tokens']:,}",
            help="Tổng số token gửi lên (System Prompt + Ảnh Biểu đồ + Dữ liệu Live)"
        )
    with col2:
        st.metric(
            label="📤 Output Tokens",
            value=f"{stats['total_output_tokens']:,}",
            help="Tổng số token AI tạo ra (Quy trình tư duy CoT + Khuyến nghị)"
        )

    # Thẻ tổng chi phí và tổng token
    total_vnd = stats['total_cost_usd'] * USD_TO_VND
    st.sidebar.markdown(
        f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 12px; margin-bottom: 10px;">
            <div style="font-size: 0.85rem; color: #94a3b8;">Tổng chi phí ước tính ({stats['calls_count']} lượt)</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #10b981;">
                ${stats['total_cost_usd']:.5f} <span style="font-size: 0.85rem; font-weight: 400; color: #cbd5e1;">(~{total_vnd:,.0f} đ)</span>
            </div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">
                Tổng Tokens: <b>{stats['total_tokens']:,}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Kỹ thuật Tối ưu Token Badge
    with st.sidebar.expander("🛡️ Kỹ thuật Tiết kiệm Token đã áp dụng", expanded=False):
        st.markdown(
            """
            - **Pillow Smart Rescaling**: Nén & chuẩn hóa ảnh về max 1024px, giảm ~65% vision tokens.
            - **Google GenAI Native Multimodal**: Xử lý trực tiếp ảnh nén tối ưu chi phí token.
            - **Pruned System Prompt**: Tối giản cấu trúc prompt CoT, loại bỏ từ thừa.
            - **Compact Market Tool Results**: Trả về dữ liệu thị trường đã lọc tinh gọn.
            """
        )

    # Bảng chi tiết từng lượt gọi nếu có lịch sử
    if stats["history"]:
        with st.sidebar.expander(f"📋 Lịch sử lượt gọi ({len(stats['history'])})", expanded=False):
            for item in reversed(stats["history"][-5:]):
                st.markdown(
                    f"**#{item['call_index']}** `{item['model']}`: "
                    f"**{item['total_tokens']:,}** tok "
                    f"*(in: {item['input_tokens']:,} | out: {item['output_tokens']:,})* "
                    f"- `${item['cost_usd']:.5f}`"
                )
            if st.button("🗑️ Xóa lịch sử Token", key="btn_reset_token", use_container_width=True):
                reset_token_stats()
                st.rerun()
