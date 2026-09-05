"""
Module: market_data.py
Cung cấp dữ liệu thị trường chứng khoán thời gian thực qua Alpha Vantage và yfinance (fallback).
Hỗ trợ tính toán các chỉ báo kỹ thuật (RSI, MA20, MA50, MA200, Hỗ trợ/Kháng cự).
"""

import os
import requests
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"


def fetch_from_alpha_vantage_quote(symbol: str, api_key: str) -> Optional[Dict[str, Any]]:
    """Lấy dữ liệu Global Quote từ Alpha Vantage."""
    if not api_key or api_key.strip() == "":
        return None
    try:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol.strip().upper(),
            "apikey": api_key.strip()
        }
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=8)
        if response.status_code == 200:
            data = response.json()
            if "Global Quote" in data and data["Global Quote"]:
                gq = data["Global Quote"]
                price = float(gq.get("05. price", 0))
                change_pct = gq.get("10. change percent", "0%").replace("%", "")
                return {
                    "source": "Alpha Vantage",
                    "symbol": symbol.upper(),
                    "current_price": price,
                    "open": float(gq.get("02. open", 0)),
                    "high": float(gq.get("03. high", 0)),
                    "low": float(gq.get("04. low", 0)),
                    "volume": int(float(gq.get("06. volume", 0))),
                    "latest_trading_day": gq.get("07. latest trading day", "N/A"),
                    "previous_close": float(gq.get("08. previous close", 0)),
                    "change": float(gq.get("09. change", 0)),
                    "change_percent": float(change_pct) if change_pct else 0.0
                }
    except Exception as e:
        print(f"[Warning] Alpha Vantage quote error: {e}")
    return None


def fetch_from_yfinance_quote(symbol: str) -> Dict[str, Any]:
    """Lấy dữ liệu thời gian thực và thông tin cơ bản từ yfinance (Fallback đáng tin cậy)."""
    symbol = symbol.strip().upper()
    ticker = yf.Ticker(symbol)
    
    # Lấy lịch sử 1 tháng để tính toán
    hist = ticker.history(period="1mo")
    if not hist.empty:
        hist = hist.dropna(subset=["Close"])
    info = {}
    try:
        info = ticker.info or {}
    except Exception:
        info = {}

    current_price = 0.0
    prev_close = 0.0
    open_price = 0.0
    high_price = 0.0
    low_price = 0.0
    volume = 0

    if not hist.empty:
        last_row = hist.iloc[-1]
        current_price = float(last_row["Close"]) if not np.isnan(last_row["Close"]) else 0.0
        high_price = float(last_row["High"]) if not np.isnan(last_row["High"]) else current_price
        low_price = float(last_row["Low"]) if not np.isnan(last_row["Low"]) else current_price
        open_price = float(last_row["Open"]) if not np.isnan(last_row["Open"]) else current_price
        volume = int(last_row["Volume"]) if not np.isnan(last_row["Volume"]) else 0
        if len(hist) > 1:
            prev_close = float(hist.iloc[-2]["Close"])
        else:
            prev_close = float(info.get("previousClose", current_price))
    else:
        current_price = float(info.get("regularMarketPrice", info.get("currentPrice", 0.0)))
        prev_close = float(info.get("previousClose", current_price))
        open_price = float(info.get("regularMarketOpen", current_price))
        high_price = float(info.get("dayHigh", current_price))
        low_price = float(info.get("dayLow", current_price))
        volume = int(info.get("regularMarketVolume", 0))

    if current_price == 0.0 and info.get("currentPrice"):
        current_price = float(info.get("currentPrice"))

    change = current_price - prev_close if prev_close else 0.0
    change_pct = (change / prev_close * 100) if prev_close else 0.0

    return {
        "source": "Yahoo Finance (Live Feed)",
        "symbol": symbol,
        "company_name": info.get("shortName", info.get("longName", symbol)),
        "current_price": round(current_price, 2),
        "open": round(open_price, 2),
        "high": round(high_price, 2),
        "low": round(low_price, 2),
        "previous_close": round(prev_close, 2),
        "change": round(change, 2),
        "change_percent": round(change_pct, 2),
        "volume": volume,
        "fifty_two_week_high": round(float(info.get("fiftyTwoWeekHigh", high_price)), 2),
        "fifty_two_week_low": round(float(info.get("fiftyTwoWeekLow", low_price)), 2),
        "currency": info.get("currency", "USD"),
        "pe_ratio": round(float(info.get("trailingPE", 0)), 2) if info.get("trailingPE") else "N/A",
        "market_cap": info.get("marketCap", "N/A")
    }


def calculate_rsi(series: pd.Series, period: int = 14) -> float:
    """Tính toán chỉ số RSI từ chuỗi giá đóng cửa."""
    if len(series) < period + 1:
        return 50.0
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0


def get_technical_indicators(symbol: str) -> Dict[str, Any]:
    """Tính toán MA20, MA50, MA200, RSI(14) và vùng hỗ trợ/kháng cự từ dữ liệu 6 tháng gần nhất."""
    symbol = symbol.strip().upper()
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="6mo")
    
    if hist.empty or len(hist) < 20:
        return {
            "symbol": symbol,
            "rsi_14": 50.0,
            "sma_20": "N/A",
            "sma_50": "N/A",
            "sma_200": "N/A",
            "support_level": "N/A",
            "resistance_level": "N/A",
            "trend_short_term": "Chưa đủ dữ liệu",
            "trend_long_term": "Chưa đủ dữ liệu"
        }

    close = hist["Close"]
    sma_20 = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else float(close.mean())
    sma_50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else float(close.mean())
    sma_200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else float(close.mean())
    rsi_14 = calculate_rsi(close, 14)
    
    current_price = float(close.iloc[-1])
    recent_30 = hist.tail(30)
    recent_min = float(recent_30["Low"].min())
    recent_max = float(recent_30["High"].max())

    short_trend = "Tăng (Bullish)" if current_price > sma_20 else "Giảm (Bearish)"
    long_trend = "Tăng dài hạn" if current_price > sma_50 else "Điều chỉnh/Giảm dài hạn"

    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "rsi_14": round(rsi_14, 2),
        "sma_20": round(sma_20, 2),
        "sma_50": round(sma_50, 2),
        "sma_200": round(sma_200, 2) if len(close) >= 200 else "N/A",
        "support_level": round(recent_min, 2),
        "resistance_level": round(recent_max, 2),
        "trend_short_term": short_trend,
        "trend_long_term": long_trend
    }


def get_stock_market_data(symbol: str, alpha_vantage_key: Optional[str] = None) -> Dict[str, Any]:
    """Hàm tổng hợp chính lấy dữ liệu giá live và chỉ báo kỹ thuật cho AI Function Calling."""
    if not alpha_vantage_key:
        alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")

    # Thử Alpha Vantage trước
    av_data = fetch_from_alpha_vantage_quote(symbol, alpha_vantage_key)
    
    # Lấy thông tin yfinance
    yf_data = fetch_from_yfinance_quote(symbol)
    tech_data = get_technical_indicators(symbol)

    # Kết hợp thông tin
    combined = {**yf_data}
    if av_data:
        combined["alpha_vantage_sync"] = True
        combined["av_price"] = av_data.get("current_price")
    else:
        combined["alpha_vantage_sync"] = False

    combined["technical_indicators"] = tech_data
    return combined


def get_stock_history_df(symbol: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
    """Lấy dữ liệu DataFrame lịch sử nến phục vụ vẽ biểu đồ Plotly tương tác."""
    try:
        ticker = yf.Ticker(symbol.strip().upper())
        df = ticker.history(period=period, interval=interval)
        if not df.empty:
            df.reset_index(inplace=True)
            return df
    except Exception as e:
        print(f"[Warning] get_stock_history_df error: {e}")
    return pd.DataFrame()


def format_market_summary_for_ai(data: Dict[str, Any]) -> str:
    """Định dạng dữ liệu thành chuỗi text ngắn gọn, tối ưu token cho AI Context."""
    sym = data.get("symbol", "UNKNOWN")
    price = data.get("current_price", "N/A")
    chg = data.get("change_percent", 0.0)
    vol = data.get("volume", "N/A")
    hi52 = data.get("fifty_two_week_high", "N/A")
    lo52 = data.get("fifty_two_week_low", "N/A")
    tech = data.get("technical_indicators", {})
    
    summary = (
        f"=== REAL-TIME MARKET DATA FOR {sym} ===\n"
        f"- Current Price: ${price} ({'+' if chg >= 0 else ''}{chg}%)\n"
        f"- Today's Range: Low ${data.get('low', 'N/A')} - High ${data.get('high', 'N/A')}\n"
        f"- 52-Week Range: ${lo52} - ${hi52}\n"
        f"- Volume: {vol:,} (PE: {data.get('pe_ratio', 'N/A')})\n"
        f"- Technical Indicators: RSI(14)={tech.get('rsi_14')}, MA20=${tech.get('sma_20')}, "
        f"MA50=${tech.get('sma_50')}, MA200=${tech.get('sma_200')}\n"
        f"- Short-term Trend: {tech.get('trend_short_term')}\n"
        f"- Key Price Levels: Support ~ ${tech.get('support_level')}, Resistance ~ ${tech.get('resistance_level')}\n"
        f"- Data Feed Status: {data.get('source', 'Live')}\n"
        f"========================================="
    )
    return summary

