"""
Test Suite: Kiểm thử toàn diện các module của ứng dụng AI Financial Assistant
(Bao gồm Google Gemini SDK & OpenAI dispatchers).
"""

import os
import sys
import unittest
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Import modules
from market_data import (
    get_stock_market_data,
    get_technical_indicators,
    get_stock_history_df,
    calculate_rsi
)
from sample_data import (
    get_sample_preset_charts,
    get_sample_image,
    generate_head_and_shoulders_data,
    generate_bullish_engulfing_data
)
from token_tracker import record_token_usage, MODEL_PRICING
from ai_agent import optimize_image_for_vision, OPENAI_TOOLS, SYSTEM_PROMPT


class TestFinancialAssistant(unittest.TestCase):

    def test_sample_chart_generation(self):
        """Kiem thu sinh bieu do nen mau."""
        presets = get_sample_preset_charts()
        self.assertIn("head_and_shoulders", presets)
        self.assertIn("bullish_engulfing", presets)
        self.assertIn("double_bottom", presets)

        img, preset = get_sample_image("head_and_shoulders")
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(preset["ticker"], "AAPL")
        self.assertGreater(img.size[0], 100)
        self.assertGreater(img.size[1], 100)
        print(f"[OK] Test Sample Chart Generation Passed: Generated {img.size} image for {preset['ticker']}")

    def test_image_token_optimization(self):
        """Kiem thu toi uu hoa anh Pillow (Token Optimizer)."""
        img = Image.new("RGB", (2560, 1440), color=(19, 23, 34))
        optimized_pil, meta = optimize_image_for_vision(img, max_dimension=1024)
        
        self.assertIsInstance(optimized_pil, Image.Image)
        self.assertLessEqual(meta["optimized_size"][0], 1024)
        self.assertLessEqual(meta["optimized_size"][1], 1024)
        self.assertGreater(meta["file_size_kb"], 0)
        print(f"[OK] Test Pillow Token Optimization Passed: Resized from {meta['original_size']} to {meta['optimized_size']}")

    def test_market_data_fetch(self):
        """Kiem thu lay du lieu gia thuc te va tinh toan chi bao RSI/MA."""
        data = get_stock_market_data("AAPL")
        self.assertIsNotNone(data)
        self.assertEqual(data["symbol"], "AAPL")
        self.assertIn("current_price", data)
        self.assertIn("technical_indicators", data)
        
        tech = data["technical_indicators"]
        self.assertIn("rsi_14", tech)
        self.assertIn("sma_20", tech)
        print(f"[OK] Test Market Data Passed: AAPL Price = ${data['current_price']}, RSI = {tech.get('rsi_14')}")

    def test_gemini_models_pricing_table(self):
        """Kiem thu bang gia mo hinh Gemini va OpenAI trong Token Tracker."""
        self.assertIn("gemini-3.7-flash", MODEL_PRICING)
        self.assertIn("gemini-2.5-flash", MODEL_PRICING)
        self.assertIn("gemini-2.5-pro", MODEL_PRICING)
        self.assertIn("gpt-4o", MODEL_PRICING)
        
        gemini_price = MODEL_PRICING["gemini-3.7-flash"]
        self.assertEqual(gemini_price["provider"], "Google Gemini")
        print(f"[OK] Test Token Pricing Table Passed: {gemini_price['name']} (${gemini_price['input_per_1m']}/M in, ${gemini_price['output_per_1m']}/M out)")

    def test_interactive_history_df(self):
        """Kiem thu nap dataframe nen lich su cho Plotly."""
        df = get_stock_history_df("AAPL", period="1mo")
        self.assertFalse(df.empty)
        self.assertIn("Close", df.columns)
        self.assertIn("Volume", df.columns)
        print(f"[OK] Test History DF Passed: Loaded {len(df)} candles for AAPL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
