"""
Diagnostic script to test google-genai syntax, contents format, and tools handling.
"""

import sys
import os
from PIL import Image
from dotenv import load_dotenv

load_dotenv(override=True)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("Checking google-genai import...")
try:
    from google import genai
    from google.genai import types
    print("[OK] google-genai imported successfully.")
except Exception as e:
    print(f"[ERROR] google-genai import error: {e}")
    sys.exit(1)

# Check API key in env
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
print(f"API Key present: {bool(api_key)}")

# Check PIL image encoding test
img = Image.new("RGB", (300, 300), color=(10, 20, 30))

try:
    client = genai.Client(api_key=api_key or "DUMMY_KEY_FOR_TESTING")
    print("[OK] genai.Client created.")
except Exception as e:
    print(f"[ERROR] genai.Client error: {e}")

# Check what types are accepted in contents
try:
    import inspect
    print("GenerateContent signature inspect:")
    sig = inspect.signature(client.models.generate_content)
    print(f"generate_content params: {list(sig.parameters.keys())}")
except Exception as e:
    print(f"Inspect error: {e}")

