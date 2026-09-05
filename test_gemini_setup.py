"""
Test script for google-genai integration with Gemini 3.7 Flash / 2.5 Flash.
"""

import sys
from PIL import Image
from market_data import get_stock_market_data, format_market_summary_for_ai

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def dummy_fetch_market_data(ticker_symbol: str) -> str:
    """Lấy dữ liệu thị trường cho ticker."""
    data = get_stock_market_data(ticker_symbol)
    return format_market_summary_for_ai(data)

print("[OK] Function defined successfully")

