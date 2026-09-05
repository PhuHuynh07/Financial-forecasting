"""
Module: sample_data.py
Tạo và cung cấp các biểu đồ nến mẫu (Candlestick Patterns) chuẩn kỹ thuật
(Head and Shoulders, Bullish Engulfing, Double Bottom, Breakout Resistance)
cho phép người dùng thử nghiệm nhanh chỉ với 1 cú click.
"""

import os
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from PIL import Image

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_charts")


def create_candlestick_image(
    df: pd.DataFrame,
    title: str = "Biểu đồ Nến Kỹ thuật",
    ticker: str = "AAPL",
    timeframe: str = "D1 (Daily)"
) -> Image.Image:
    """Vẽ biểu đồ nến bằng matplotlib và trả về ảnh PIL chất lượng cao."""
    fig, (ax, ax_vol) = plt.subplots(
        2, 1, figsize=(10, 6),
        gridspec_kw={"height_ratios": [3, 1]},
        facecolor="#131722"
    )
    
    ax.set_facecolor("#131722")
    ax_vol.set_facecolor("#131722")

    # Màu nến theo chuẩn TradingView
    up_color = "#089981"    # Xanh lá
    down_color = "#f23645"  # Đỏ

    width = 0.6
    width2 = 0.1

    for idx, row in df.iterrows():
        open_val = row["Open"]
        close_val = row["Close"]
        high_val = row["High"]
        low_val = row["Low"]
        color = up_color if close_val >= open_val else down_color
        
        # Vẽ bấc nến (wick)
        ax.plot([idx, idx], [low_val, high_val], color=color, linewidth=1.2)
        # Vẽ thân nến (body)
        ax.bar(
            idx, abs(close_val - open_val),
            bottom=min(open_val, close_val),
            color=color, width=width, edgecolor=color
        )

        # Vẽ Volume
        vol_color = up_color if close_val >= open_val else down_color
        ax_vol.bar(idx, row["Volume"], color=vol_color, width=width, alpha=0.8)

    # Đường trung bình động MA20
    if "MA20" in df.columns:
        ax.plot(df.index, df["MA20"], color="#2962ff", linewidth=1.4, label="MA20", alpha=0.9)
    if "MA50" in df.columns:
        ax.plot(df.index, df["MA50"], color="#ff9800", linewidth=1.4, label="MA50", alpha=0.9)

    ax.set_title(
        f"{ticker} • {timeframe} — {title}",
        color="#d1d4dc", fontsize=13, fontweight="bold", pad=12, loc="left"
    )
    ax.grid(True, color="#2a2e39", linestyle="--", linewidth=0.6, alpha=0.7)
    ax_vol.grid(True, color="#2a2e39", linestyle="--", linewidth=0.6, alpha=0.7)

    # Tùy chỉnh trục tọa độ
    ax.tick_params(colors="#787b86", labelsize=9)
    ax_vol.tick_params(colors="#787b86", labelsize=8)
    ax.spines['bottom'].set_color('#2a2e39')
    ax.spines['top'].set_color('#2a2e39')
    ax.spines['right'].set_color('#2a2e39')
    ax.spines['left'].set_color('#2a2e39')
    ax_vol.spines['bottom'].set_color('#2a2e39')
    ax_vol.spines['top'].set_color('#2a2e39')
    ax_vol.spines['right'].set_color('#2a2e39')
    ax_vol.spines['left'].set_color('#2a2e39')
    
    ax.legend(loc="upper left", facecolor="#1e222d", edgecolor="#2a2e39", labelcolor="#d1d4dc", fontsize=9)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)


def generate_head_and_shoulders_data() -> pd.DataFrame:
    """Tạo chuỗi nến mô phỏng mô hình Head and Shoulders (Vai - Đầu - Vai Đảo chiều Giảm)."""
    np.random.seed(42)
    # 45 nến: Tăng lên Left Shoulder -> Giảm xuống Neckline -> Tăng lên Head -> Giảm xuống Neckline -> Tăng lên Right Shoulder -> Phá vỡ Neckline
    prices = [
        150, 152, 155, 158, 162, 168, 172, 175, 174, 170, # Left shoulder peak ~175
        164, 160, 158, 159, 163, 170, 178, 184, 188, 187, # Head peak ~188
        182, 175, 168, 160, 158, 159, 164, 172, 174, 173, # Right shoulder peak ~174
        168, 162, 158, 154, 149, 145, 142, 140, 138, 136  # Breakdown neckline ~158 -> 136
    ]
    
    rows = []
    for i, p in enumerate(prices):
        noise = np.random.uniform(-1.2, 1.2)
        p_adj = p + noise
        body_size = np.random.uniform(0.8, 3.0)
        is_green = (i < 8) or (13 < i < 19) or (25 < i < 29)
        if is_green:
            o = p_adj - body_size / 2
            c = p_adj + body_size / 2
        else:
            o = p_adj + body_size / 2
            c = p_adj - body_size / 2
        h = max(o, c) + np.random.uniform(0.3, 1.8)
        l = min(o, c) - np.random.uniform(0.3, 1.8)
        vol = int(np.random.uniform(30000000, 70000000))
        if i in [7, 18, 28, 34]:  # Volume cao tại các đỉnh và điểm phá vỡ
            vol *= 2
        rows.append({"Open": o, "High": h, "Low": l, "Close": c, "Volume": vol})

    df = pd.DataFrame(rows)
    df["MA20"] = df["Close"].rolling(10, min_periods=1).mean()
    df["MA50"] = df["Close"].rolling(20, min_periods=1).mean()
    return df


def generate_bullish_engulfing_data() -> pd.DataFrame:
    """Tạo chuỗi nến mô phỏng mô hình Bullish Engulfing (Nhấn chìm Tăng trưởng tại Vùng Hỗ trợ)."""
    np.random.seed(101)
    # Xu hướng giảm liên tục -> Nến đỏ nhỏ -> Nến xanh khổng lồ nhấn chìm toàn bộ nến trước -> Tăng tiếp
    prices = [
        220, 216, 212, 208, 202, 196, 190, 185, 180, 176,
        172, 170, 168, 166, 165, 164, 163, # Nến đỏ nhỏ tại đáy
        172, 178, 184, 190, 195, 202, 210  # Nến xanh nhấn chìm (Engulfing) và bật mạnh
    ]
    
    rows = []
    for i, p in enumerate(prices):
        if i == 16:  # Nến đỏ nhỏ cuối cùng
            o, c = 164.5, 163.0
            h, l = 165.2, 162.0
            vol = 25000000
        elif i == 17:  # Nến Bullish Engulfing bao phủ
            o, c = 162.2, 172.5  # Mở dưới đáy nến trước, đóng cao hơn đỉnh nến trước
            h, l = 173.0, 161.8
            vol = 85000000  # Đột biến khối lượng
        else:
            is_green = i > 17
            noise = np.random.uniform(-0.8, 0.8)
            base = p + noise
            if is_green:
                o, c = base - 1.5, base + 1.5
            else:
                o, c = base + 1.5, base - 1.5
            h = max(o, c) + np.random.uniform(0.5, 1.5)
            l = min(o, c) - np.random.uniform(0.5, 1.5)
            vol = int(np.random.uniform(20000000, 45000000))
        
        rows.append({"Open": o, "High": h, "Low": l, "Close": c, "Volume": vol})

    df = pd.DataFrame(rows)
    df["MA20"] = df["Close"].rolling(8, min_periods=1).mean()
    df["MA50"] = df["Close"].rolling(15, min_periods=1).mean()
    return df


def generate_double_bottom_data() -> pd.DataFrame:
    """Tạo chuỗi nến mô phỏng mô hình Double Bottom (Hai đáy W Đảo chiều Tăng)."""
    np.random.seed(202)
    # Giảm xuống Đáy 1 (140) -> Bật lên Neckline (155) -> Giảm xuống Đáy 2 (140.5) -> Breakout Neckline (165)
    prices = [
        170, 165, 158, 152, 145, 141, 140, 140.5, # Bottom 1
        144, 148, 152, 155, 156, 154, 150,        # Neckline peak
        145, 142, 140.5, 141, 143,                # Bottom 2
        148, 153, 157, 162, 168, 174, 180         # Breakout & Rally
    ]
    rows = []
    for i, p in enumerate(prices):
        is_green = (6 <= i <= 12) or (18 <= i)
        o = p - 1.2 if is_green else p + 1.2
        c = p + 1.2 if is_green else p - 1.2
        h = max(o, c) + np.random.uniform(0.4, 1.6)
        l = min(o, c) - np.random.uniform(0.4, 1.6)
        vol = int(np.random.uniform(25000000, 55000000))
        if i in [6, 18, 22]:
            vol *= 1.8
        rows.append({"Open": o, "High": h, "Low": l, "Close": c, "Volume": vol})

    df = pd.DataFrame(rows)
    df["MA20"] = df["Close"].rolling(8, min_periods=1).mean()
    df["MA50"] = df["Close"].rolling(15, min_periods=1).mean()
    return df


def get_sample_preset_charts() -> dict:
    """Tạo hoặc trả về danh sách các biểu đồ nến mẫu kèm thông tin cấu hình."""
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    
    samples = {
        "head_and_shoulders": {
            "name": "Mô hình Vai - Đầu - Vai (Head & Shoulders) — AAPL",
            "ticker": "AAPL",
            "pattern_expected": "Head and Shoulders (Đảo chiều Giảm Bearish)",
            "generator": generate_head_and_shoulders_data,
            "description": "Mô hình đảo chiều kinh điển gồm Vai Trái, Đỉnh Đầu cao hơn, Vai Phải và đường Cổ (Neckline) bị phá vỡ xuống dưới."
        },
        "bullish_engulfing": {
            "name": "Mô hình Nến Nhấn Chìm Tăng (Bullish Engulfing) — NVDA",
            "ticker": "NVDA",
            "pattern_expected": "Bullish Engulfing (Đảo chiều Tăng Mạnh)",
            "generator": generate_bullish_engulfing_data,
            "description": "Nến xanh thân dài xuất hiện tại đáy xu hướng giảm, bao trùm hoàn toàn thân nến đỏ trước đó kèm khối lượng tăng vọt."
        },
        "double_bottom": {
            "name": "Mô hình Hai Đáy (Double Bottom / Chữ W) — TSLA",
            "ticker": "TSLA",
            "pattern_expected": "Double Bottom (Đảo chiều Tăng Bullish)",
            "generator": generate_double_bottom_data,
            "description": "Hai đáy liên tiếp tại cùng một vùng hỗ trợ mạnh tạo hình chữ W, phá vỡ đường kháng cự Neckline để bước vào xu hướng tăng mới."
        }
    }
    return samples


def get_sample_image(sample_key: str) -> tuple[Image.Image, dict]:
    """Lấy ảnh PIL và metadata của biểu đồ mẫu được chọn."""
    presets = get_sample_preset_charts()
    if sample_key not in presets:
        sample_key = "head_and_shoulders"
    
    preset = presets[sample_key]
    df = preset["generator"]()
    img = create_candlestick_image(
        df=df,
        title=preset["name"],
        ticker=preset["ticker"],
        timeframe="D1"
    )
    return img, preset

