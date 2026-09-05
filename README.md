# 📈 AI Financial Analyst Pro — Trợ lý Phân tích Tài chính Tự động

Ứng dụng Web App cao cấp phát triển bằng **Python Streamlit** và **OpenAI GPT-4o**, đóng vai trò là Trợ lý Phân tích Kỹ thuật & Dữ liệu Thị trường Thông minh cho các nhà đầu tư cá nhân.

---

## 🌟 Tính Năng Nổi Bật

### 1. 👁️ Phân Tích Biểu Đồ Nến Thị Giác (Computer Vision)
- Nhận diện các mô hình giá kinh điển: **Head and Shoulders (Vai - Đầu - Vai)**, **Bullish/Bearish Engulfing (Nhấn chìm Tăng/Giảm)**, **Double Bottom/Top (Hai Đáy/Hai Đỉnh)**, **Tam giác Tích lũy (Triangles)**, v.v.
- Tự động phát hiện mã cổ phiếu (Ticker Symbol), khung thời gian (Timeframe), các đường xu hướng (Trendlines) và vùng hỗ trợ/kháng cự từ ảnh chụp màn hình biểu đồ (TradingView, MT5, TCBS, SSI, FireAnt...).

### 2. 🤖 Tác Vụ Tự Động Hóa Agentic (OpenAI Function Calling)
- Sau khi "nhìn" và trích xuất mã cổ phiếu từ biểu đồ ảnh, AI tự động kích hoạt **Agent Tool (`fetch_realtime_market_data`)**.
- Tích hợp trực tiếp với API **Alpha Vantage** kèm cơ chế **Yahoo Finance Live Feed fallback**, lấy giá thời gian thực, khối lượng giao dịch, biên độ 52 tuần, chỉ báo RSI(14) và các đường trung bình MA20/MA50/MA200.
- Đối chiếu sự khác biệt giữa mô hình kỹ thuật trong quá khứ trên ảnh với diễn biến giá thực tế hiện tại.

### 3. 🧠 Suy Luận Chuỗi Tư Duy (Chain of Thought — CoT)
- Trình bày trực quan phần **"Quy trình tư duy"** của AI theo từng bước logic:
  1. Khảo sát hình học đỉnh/đáy và tỷ lệ nến.
  2. Xác nhận qua khối lượng giao dịch (Volume) và đường viền cổ (Neckline).
  3. Đối chiếu dữ liệu thị trường thực tế.
  4. Tính toán tỷ lệ Lợi nhuận/Rủi ro (Risk:Reward) và xác lập kế hoạch vào lệnh (Entry, Take Profit, Stop Loss).

### 4. ⚡ Quản Lý Token AI & Chi Phí Real-time (Token Telemetry)
- **Cấu hình API Key**: Tự động nạp qua `.env` hoặc nhập trực tiếp an toàn trên thanh Sidebar của Streamlit.
- **Sidebar Telemetry Dashboard**: Hiển thị thời gian thực số lượng **Input Tokens**, **Output Tokens**, **Tổng Tokens** và **Chi phí ước tính ($USD và VND)** sau mỗi lượt phân tích.
- **Kỹ thuật Tối ưu hóa Token**:
  - Tự động nén và resize ảnh thông minh bằng **Pillow** (giảm 60-70% Vision tokens).
  - Tối ưu cấu trúc System Prompt tinh gọn, loại bỏ token dư thừa.
  - Tùy chọn chế độ độ chi tiết Vision (`auto`, `low`, `high`).

### 5. 🎯 Thư Viện Biểu Đồ Mẫu & Đồ Thị Tương Tác (Plotly)
- Tích hợp sẵn 3 mô hình nến mẫu chuẩn kỹ thuật (**Head and Shoulders**, **Bullish Engulfing**, **Double Bottom**) cho phép người dùng kiểm thử ngay chỉ với 1 cú click.
- Đồ thị nến tương tác Plotly đa khung thời gian kết hợp khối lượng và các đường MA.
- Hỗ trợ xuất và tải báo cáo phân tích định dạng Markdown (`.md`).

---

## 🛠️ Cài Đặt & Chạy Ứng Dụng

### 1. Chuẩn bị Môi trường
Cài đặt thư viện bằng `uv` hoặc `pip`:
```bash
# Cách 1: Sử dụng uv (Khuyên dùng)
uv venv --python 3.12
uv pip install -r requirements.txt

# Cách 2: Sử dụng pip chuẩn
python -m venv .venv
.venv\Scripts\activate      # Trên Windows
# source .venv/bin/activate # Trên Linux / macOS
pip install -r requirements.txt
```

### 2. Cấu hình API Key (.env)
Tạo file `.env` từ `.env.example`:
```env
OPENAI_API_KEY=sk-...your-openai-api-key...
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key-optional
OPENAI_MODEL=gpt-4o
```
*(Bạn cũng có thể nhập API Key trực tiếp trên thanh Sidebar của giao diện web).*

### 3. Khởi Chạy Ứng Dụng
```bash
uv run streamlit run app.py
```
Ứng dụng sẽ tự động mở tại địa chỉ: `http://localhost:8501`.

---

## 🧪 Kiểm Thử Tự Động (Test Suite)
Chạy bộ kiểm thử để xác minh tính toàn vẹn của tất cả các module:
```bash
uv run python test_suite.py
```

---

## 📁 Cấu Trúc Dự Án
```
├── app.py              # File chạy chính của giao diện Streamlit
├── ai_agent.py         # Bộ não AI: GPT-4o Vision + Function Calling + CoT
├── market_data.py      # Dữ liệu thị trường: Alpha Vantage & yfinance fallback
├── token_tracker.py    # Quản lý & hiển thị Token / Cost telemetry real-time
├── sample_data.py      # Thư viện sinh biểu đồ nến mẫu (Head & Shoulders, Engulfing...)
├── styles.css          # Giao diện Fintech Glassmorphism hiện đại
├── test_suite.py       # Bộ test tự động các module
├── requirements.txt    # Danh sách các thư viện phụ thuộc
├── .env.example        # Mẫu file cấu hình môi trường
└── .env                # File cấu hình API Keys cá nhân
```

