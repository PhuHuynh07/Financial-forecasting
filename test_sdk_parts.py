"""
Test image part and function calling config serialization in google-genai.
"""

import sys
import io
from PIL import Image
from google import genai
from google.genai import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

client = genai.Client(api_key="TEST_API_KEY")

img = Image.new("RGB", (100, 100), color=(255, 0, 0))
buf = io.BytesIO()
img.save(buf, format="JPEG")
img_bytes = buf.getvalue()

# Test 1: PIL Image vs Part.from_bytes
part_from_bytes = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
print("[OK] types.Part.from_bytes created:", type(part_from_bytes))

# Test 2: Function Calling Tool definition
def sample_tool(ticker_symbol: str) -> str:
    """Get market data for ticker.
    
    Args:
        ticker_symbol: The stock ticker symbol.
    """
    return f"Data for {ticker_symbol}"

config = types.GenerateContentConfig(
    tools=[sample_tool],
    temperature=0.2
)
print("[OK] GenerateContentConfig with Python function tool created:", type(config))

