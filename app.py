"""
Trợ lý Phân tích Tài chính Tự động (AI Financial Analysis Assistant)
Ứng dụng Web App Streamlit kết hợp Google Gemini (Gemini 3.6 Flash / 3.7 Flash) / OpenAI
kèm Chế độ Demo Thử nghiệm ngay không cần API Key.
"""

import os
import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
from dotenv import load_dotenv

# Tự động nạp và ghi đè biến môi trường từ file .env
load_dotenv(override=True)

# Nạp các module tự phát triển
from market_data import get_stock_market_data, get_stock_history_df
from token_tracker import init_token_state, render_sidebar_token_tracker
from sample_data import get_sample_preset_charts, get_sample_image
from ai_agent import execute_financial_agent_pipeline, optimize_image_for_vision

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="AI Financial Analyst Pro | Gemini 3.6 Flash",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Nạp Custom CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()
init_token_state()

# ----------------- SIDEBAR CẤU HÌNH & TOKEN TRACKER -----------------
with st.sidebar:
    st.markdown("### ⚙️ Cấu hình Nhà Cung Cấp AI")
    
    # 1. Chọn Nhà cung cấp AI
    selected_provider = st.radio(
        "Lựa chọn AI Engine:",
        options=[
            "🔵 Google Gemini (Khuyên dùng)",
            "🟢 OpenAI (GPT-4o)",
            "🧪 Chế độ Demo (Không cần API Key)"
        ],
        index=0,
        help="Google Gemini: Miễn phí, tốc độ cao với Gemini 3.6 Flash. OpenAI: Trả phí theo credit. Chế độ Demo: Dùng thử nghiệm ngay không cần key."
    )

    api_key_input = ""
    selected_model = "gemini-3.6-flash"

    # 2. Xử lý trường nhập API Key theo từng lựa chọn
    if "Google Gemini" in selected_provider:
        env_gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        api_key_input = st.text_input(
            "Google Gemini API Key:",
            value=env_gemini_key,
            type="password",
            help="Dán Google Gemini API Key của bạn (thường bắt đầu bằng AIzaSy...)"
        )
        st.markdown(
            """
            <div style="font-size: 0.82rem; color: #94a3b8; margin-top: -6px; margin-bottom: 12px;">
                🔑 <i>Lấy Key Miễn Phí tại:</i> <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color: #38bdf8; text-decoration: underline;">Google AI Studio</a>
            </div>
            """,
            unsafe_allow_html=True
        )
        selected_model = st.selectbox(
            "Mô hình Gemini:",
            options=["gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite", "gemini-3.1-pro-preview"],
            index=0,
            help="gemini-3.6-flash: Mô hình chính thức mới nhất, tốc độ siêu nhanh, nhận diện nến và Tool Calling hoàn hảo."
        )

        if api_key_input and api_key_input.strip():
            if api_key_input.strip().startswith("sk-"):
                st.warning("⚠️ Đây là OpenAI API Key. Vui lòng chuyển sang mục 'OpenAI' hoặc dùng key 'AIzaSy...'.")
            else:
                st.success("✅ Google Gemini Key đã sẵn sàng", icon="🟢")
        else:
            st.warning("⚠️ Chưa nhập Google Gemini API Key", icon="🟡")

    elif "OpenAI" in selected_provider:
        env_openai_key = os.getenv("OPENAI_API_KEY", "")
        api_key_input = st.text_input(
            "OpenAI API Key:",
            value=env_openai_key,
            type="password",
            help="Dán OpenAI API Key của bạn (sk-...)"
        )
        st.markdown(
            """
            <div style="font-size: 0.82rem; color: #94a3b8; margin-top: -6px; margin-bottom: 12px;">
                🔑 <i>Lấy Key tại:</i> <a href="https://platform.openai.com/api-keys" target="_blank" style="color: #38bdf8; text-decoration: underline;">OpenAI Platform</a>
            </div>
            """,
            unsafe_allow_html=True
        )
        selected_model = st.selectbox(
            "Mô hình OpenAI:",
            options=["gpt-4o", "gpt-4o-mini"],
            index=0
        )

        if api_key_input and api_key_input.strip():
            if api_key_input.strip().startswith("AIzaSy"):
                st.warning("⚠️ Đây là Google Gemini API Key. Vui lòng chuyển sang mục 'Google Gemini'.")
            else:
                st.success("✅ OpenAI API Key đã sẵn sàng", icon="🟢")
        else:
            st.warning("⚠️ Chưa nhập OpenAI API Key", icon="🟡")

    else:  # Chế độ Demo
        st.info("🧪 **Đang kích hoạt Chế độ Demo:** Bạn có thể phân tích biểu đồ, lấy dữ liệu giá live và xem Chain of Thought mà không cần bất kỳ API Key nào!")
        selected_model = "gemini-3.6-flash"
        api_key_input = "DEMO_MODE"

    # 3. Alpha Vantage API Key (Tùy chọn)
    env_av_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    av_key_input = st.text_input(
        "Alpha Vantage Key (Tùy chọn):",
        value=env_av_key,
        type="password",
        help="Nếu để trống, AI sẽ tự động lấy giá live từ Yahoo Finance Feed hoàn toàn miễn phí"
    )

    # 4. Hiển thị Widget Token Tracker Real-time
    render_sidebar_token_tracker(current_model=selected_model)


# ----------------- GIAO DIỆN CHÍNH -----------------
st.markdown(
    """
    <div class="fintech-header">
        <h1 class="fintech-title">📈 AI Financial Analyst Pro</h1>
        <div class="fintech-subtitle">
            Trợ lý Phân tích Kỹ thuật & Dữ liệu Thị trường Tự động bằng <b>Google Gemini 3.6 Flash / GPT-4o (Vision + Tool Calling + Chain of Thought)</b>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Khởi tạo session state lưu kết quả phân tích
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = ""

# Tự động nạp biểu đồ mẫu mặc định nếu người dùng chưa chọn ảnh nào
sample_presets = get_sample_preset_charts()
if st.session_state.current_image is None:
    default_img, default_preset = get_sample_image("head_and_shoulders")
    st.session_state.current_image = default_img
    st.session_state.current_ticker = default_preset["ticker"]
    st.session_state.image_source_name = default_preset["name"]

# Layout 2 cột: Upload/Chọn ảnh & Cấu hình nhanh
col_input, col_preview = st.columns([1.1, 0.9], gap="medium")

with col_input:
    st.subheader("1. Nạp Biểu đồ Nến (Candlestick Chart)")
    
    input_tab1, input_tab2 = st.tabs(["🎯 Chọn Biểu đồ Mẫu Kỹ thuật", "📁 Tải ảnh từ máy tính"])
    
    with input_tab1:
        preset_choice = st.selectbox(
            "Danh mục mô hình nến mẫu:",
            options=list(sample_presets.keys()),
            format_func=lambda k: sample_presets[k]["name"],
            index=0
        )
        selected_preset = sample_presets[preset_choice]
        st.info(f"💡 **Đặc điểm mô hình:** {selected_preset['description']}")
        
        # Tự động cập nhật ảnh khi người dùng chọn trong dropdown
        if st.session_state.get("last_preset_choice") != preset_choice:
            img, preset = get_sample_image(preset_choice)
            st.session_state.current_image = img
            st.session_state.current_ticker = preset["ticker"]
            st.session_state.image_source_name = preset["name"]
            st.session_state["last_preset_choice"] = preset_choice

    with input_tab2:
        uploaded_file = st.file_uploader(
            "Tải ảnh chụp màn hình biểu đồ nến (TradingView, FireAnt, TCBS, MT5,...)",
            type=["png", "jpg", "jpeg", "webp"],
            help="Hỗ trợ định dạng PNG, JPG, WEBP. Ảnh sẽ được tự động tối ưu hóa kích thước trước khi gửi tới AI."
        )
        if uploaded_file is not None:
            st.session_state.current_image = Image.open(uploaded_file)
            st.session_state.image_source_name = uploaded_file.name

    st.markdown("---")
    st.subheader("2. Thông tin Bổ sung (Tùy chọn)")
    ticker_input = st.text_input(
        "Mã cổ phiếu / Ticker (nếu không nhập, AI sẽ tự động đọc từ biểu đồ):",
        value=st.session_state.current_ticker,
        placeholder="Ví dụ: AAPL, NVDA, TSLA, MSFT, BTC-USD, SPY..."
    )
    if ticker_input:
        st.session_state.current_ticker = ticker_input.strip().upper()

    analyze_button = st.button(
        "🚀 Khởi chạy Phân tích Đa tầng (AI Vision + Live API)",
        type="primary",
        use_container_width=True
    )

with col_preview:
    st.subheader("🖼️ Xem trước Biểu đồ & Tối ưu Token")
    if st.session_state.current_image is not None:
        caption_text = f"Ảnh biểu đồ: {st.session_state.get('image_source_name', 'Đã nạp')}"
        st.image(st.session_state.current_image, caption=caption_text, use_container_width=True)
        
        # Thống kê Pillow Token Optimization
        _, img_meta = optimize_image_for_vision(st.session_state.current_image)
        st.markdown(
            f"""
            <div style="background: rgba(30, 41, 59, 0.5); border-radius: 8px; padding: 10px; font-size: 0.85rem; color: #94a3b8;">
                📐 Kích thước gốc: <b>{img_meta['original_size'][0]}x{img_meta['original_size'][1]}</b> | 
                🚀 Đã tối ưu về: <b>{img_meta['optimized_size'][0]}x{img_meta['optimized_size'][1]}</b> (~{img_meta['file_size_kb']} KB)
                <br>✨ Tiết kiệm ước tính: <b>~65% Vision Tokens</b> so với ảnh raw.
            </div>
            """,
            unsafe_allow_html=True
        )


# ----------------- XỬ LÝ PHÂN TÍCH AGENTIC -----------------
if analyze_button:
    if st.session_state.current_image is None:
        st.error("⚠️ Vui lòng tải ảnh biểu đồ hoặc chọn biểu đồ mẫu trước khi phân tích!")
    elif "Demo" not in selected_provider and (not api_key_input or not api_key_input.strip()):
        st.error(f"⚠️ Chưa có API Key! Vui lòng nhập API Key trên Sidebar, hoặc chọn **'🧪 Chế độ Demo (Không cần API Key)'** để chạy thử nghiệm ngay!")
    else:
        with st.status("🤖 AI Agent đang thực thi quy trình phân tích đa tầng...", expanded=True) as status_widget:
            def update_status(msg: str):
                status_widget.write(f"👉 {msg}")

            try:
                result = execute_financial_agent_pipeline(
                    image=st.session_state.current_image,
                    provider=selected_provider,
                    user_ticker=st.session_state.current_ticker,
                    api_key=api_key_input,
                    alpha_vantage_key=av_key_input,
                    model_name=selected_model,
                    status_callback=update_status
                )
                st.session_state.analysis_result = result
                status_widget.update(label="✅ Phân tích hoàn tất thành công!", state="complete", expanded=False)
            except Exception as e:
                err_msg = str(e)
                status_widget.update(label=f"❌ Lỗi thực thi", state="error", expanded=True)
                if "API_KEY_INVALID" in err_msg or "API key not valid" in err_msg or "Incorrect API key" in err_msg:
                    st.error("❌ **API Key không hợp lệ:** Vui lòng kiểm tra lại Key đã copy đúng chưa, hoặc chuyển sang **Chế độ Demo** để dùng thử.")
                elif "404" in err_msg or "not found" in err_msg.lower():
                    st.error("❌ **Model không khả dụng (404):** Hệ thống đã tự động chuyển sang `gemini-3.6-flash`. Vui lòng bấm thử lại.")
                elif "503" in err_msg or "overloaded" in err_msg.lower():
                    st.error("❌ **Máy chủ AI tạm thời quá tải (503):** Vui lòng thử lại sau vài giây.")
                elif "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                    st.error("❌ **Hạn mức API đã hết (Rate Limit / Quota):** Vui lòng thử lại sau hoặc chuyển sang Chế độ Demo.")
                else:
                    st.error(f"❌ **Chi tiết lỗi:** {err_msg}")


# ----------------- HIỂN THỊ KẾT QUẢ PHÂN TÍCH -----------------
if st.session_state.analysis_result is not None:
    res = st.session_state.analysis_result
    mdata = res.get("market_data")
    tusage = res.get("token_usage", {})
    provider_name = res.get("provider", "AI Engine")
    
    st.markdown("---")
    st.markdown("## 📊 KẾT QUẢ PHÂN TÍCH TÀI CHÍNH TỰ ĐỘNG")

    # Banner Tóm tắt Token Lượt này
    st.markdown(
        f"""
        <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 12px 18px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <b>🎯 Mã cổ phiếu nhận diện:</b> <span style="font-size: 1.25rem; color: #38bdf8; font-weight: 700;">{res.get('detected_symbol', 'N/A')}</span>
                <span style="font-size: 0.85rem; color: #94a3b8; margin-left: 12px;">(Engine: <b>{provider_name}</b>)</span>
            </div>
            <div style="font-size: 0.9rem; color: #cbd5e1;">
                ⚡ Token lượt này: <b>{tusage.get('total_tokens', 0):,}</b> 
                (Input: <b>{tusage.get('prompt_tokens', 0):,}</b> | Output: <b>{tusage.get('completion_tokens', 0):,}</b>) — Chi phí: <b style="color: #10b981;">${tusage.get('cost_usd', 0):.5f}</b> (~{tusage.get('cost_vnd', 0):,.0f}đ)
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1. Thẻ số liệu thị trường thực tế (Live Market Metrics)
    if mdata:
        st.subheader("⚡ Dữ liệu Thị trường Thực tế (Live Data Fetch via Agent Tool)")
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        
        with mcol1:
            chg = mdata.get('change_percent', 0.0)
            chg_val = mdata.get('change', 0.0)
            st.metric(
                label=f"Giá hiện tại ({mdata.get('symbol')})",
                value=f"${mdata.get('current_price', 0):,.2f}",
                delta=f"{'+' if chg >= 0 else ''}{chg_val:.2f} ({chg:.2f}%)"
            )
        
        with mcol2:
            tech = mdata.get("technical_indicators", {})
            rsi = tech.get("rsi_14", 50.0)
            rsi_status = "Quá mua" if rsi >= 70 else ("Quá bán" if rsi <= 30 else "Trung tính")
            st.metric(
                label="Chỉ số RSI (14)",
                value=f"{rsi:.2f}",
                delta=rsi_status,
                delta_color="off" if rsi_status == "Trung tính" else ("inverse" if rsi >= 70 else "normal")
            )

        with mcol3:
            st.metric(
                label="Biên độ Ngày (Day Range)",
                value=f"${mdata.get('low', 0):,.2f} - ${mdata.get('high', 0):,.2f}"
            )

        with mcol4:
            st.metric(
                label="Biên độ 52 Tuần (52W Range)",
                value=f"${mdata.get('fifty_two_week_low', 0):,.2f} - ${mdata.get('fifty_two_week_high', 0):,.2f}"
            )

    # 2. Báo cáo Chi tiết từ AI: Tách Chain of Thought và Khuyến nghị
    st.subheader("🧠 Báo cáo Phân tích Chuyên sâu (AI Chief Analyst Report)")
    
    full_report = res.get("analysis_report", "")

    # Hiển thị toàn bộ báo cáo với phong cách Markdown chỉn chu
    st.markdown(full_report)

    # 3. Biểu đồ Nến Tương tác Real-time Plotly
    if mdata and mdata.get("symbol"):
        symbol_for_chart = mdata.get("symbol")
        st.markdown("---")
        st.subheader(f"📈 Biểu đồ Kỹ thuật Tương tác Real-time: {symbol_for_chart}")
        
        with st.spinner("Đang tải dữ liệu nến tương tác..."):
            hist_df = get_stock_history_df(symbol_for_chart, period="6mo", interval="1d")
            
            if not hist_df.empty:
                # Vẽ biểu đồ tương tác nến + MA20/MA50 + Volume
                hist_df["MA20"] = hist_df["Close"].rolling(20).mean()
                hist_df["MA50"] = hist_df["Close"].rolling(50).mean()

                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.04,
                    row_heights=[0.75, 0.25],
                    subplot_titles=(f"Diễn biến Giá & Các Đường Trung Bình Động ({symbol_for_chart})", "Khối Lượng Giao Dịch (Volume)")
                )

                # Nến OHLC
                fig.add_trace(
                    go.Candlestick(
                        x=hist_df["Date"],
                        open=hist_df["Open"],
                        high=hist_df["High"],
                        low=hist_df["Low"],
                        close=hist_df["Close"],
                        name="Nến Giá",
                        increasing_line_color='#089981',
                        decreasing_line_color='#f23645'
                    ),
                    row=1, col=1
                )

                # MA20 & MA50
                fig.add_trace(
                    go.Scatter(
                        x=hist_df["Date"], y=hist_df["MA20"],
                        line=dict(color="#38bdf8", width=1.5),
                        name="MA20 (Ngắn hạn)"
                    ),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=hist_df["Date"], y=hist_df["MA50"],
                        line=dict(color="#fbbf24", width=1.5),
                        name="MA50 (Trung hạn)"
                    ),
                    row=1, col=1
                )

                # Volume Bar
                colors = ['#089981' if c >= o else '#f23645' for o, c in zip(hist_df['Open'], hist_df['Close'])]
                fig.add_trace(
                    go.Bar(
                        x=hist_df["Date"],
                        y=hist_df["Volume"],
                        marker_color=colors,
                        name="Volume",
                        opacity=0.8
                    ),
                    row=2, col=1
                )

                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#0f172a",
                    plot_bgcolor="#0f172a",
                    height=550,
                    margin=dict(l=20, r=20, t=40, b=20),
                    xaxis_rangeslider_visible=False,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255, 255, 255, 0.08)')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255, 255, 255, 0.08)')

                st.plotly_chart(fig, use_container_width=True)

    # 4. Xuất Báo cáo (Download)
    st.markdown("---")
    st.download_button(
        label="📥 Tải xuống Báo cáo Phân tích (Markdown)",
        data=full_report,
        file_name=f"AI_Financial_Report_{res.get('detected_symbol', 'STOCK')}.md",
        mime="text/markdown",
        use_container_width=True
    )
