"""Tests for Firebase Bridge - message parsing functions only (no Firebase needed)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firebase_bridge import (
    detect_market,
    detect_type,
    extract_title,
    extract_preview,
    extract_stock_info,
)


def test_detect_market_always_us_short_message():
    """US-only runtime: arbitrary body text still classifies as ``us``."""
    msg = "Intraday move on sample ticker (+5.2%)"
    assert detect_market(msg) == "us"

    msg2 = "Sample macro headline copied from overseas channel"
    assert detect_market(msg2) == "us"


def test_detect_market_us():
    """US market detection."""
    msg = "AAPL earnings beat expectations. $198.50 (+3.2%)"
    assert detect_market(msg) == "us"


def test_detect_type_trigger():
    """Explicit prism/trigger phrasing resolves before generic analysis keywords."""
    msg = "US Stock Morning Prism Signal Alert — ticker XYZ"
    assert detect_type(msg) == "trigger"


def test_detect_type_analysis():
    """Analysis type detection."""
    msg = "Market analysis summary — constructive tone on macro"
    assert detect_type(msg) == "analysis"


def test_detect_type_portfolio():
    """Portfolio type detection."""
    msg = "Portfolio summary: diversified across growth + value sleeves"
    assert detect_type(msg) == "portfolio"


def test_detect_type_pdf():
    """PDF type detection (.pdf substring before other keywords)."""
    msg = "AAPL_20260301_report.pdf uploaded"
    assert detect_type(msg) == "pdf"


def test_extract_title():
    """Title extraction."""
    msg = "NVDA breakout watch\nVolume elevated\nMomentum signal flagged"
    title = extract_title(msg)
    assert title == "NVDA breakout watch"

    msg2 = "\n---\nActual headline\nBody"
    assert extract_title(msg2) == "Actual headline"


def test_extract_title_markdown():
    """Title extraction with markdown."""
    msg = "**NVDA** breakout watch — volume elevated"
    title = extract_title(msg)
    assert "NVDA" in title
    assert "*" not in title


def test_extract_preview_short():
    """Preview extraction for short messages."""
    msg = "Short note."
    assert extract_preview(msg) == "Short note."


def test_extract_preview_long():
    """Preview extraction for long messages - truncated to 100 chars."""
    msg = "A" * 200
    preview = extract_preview(msg)
    assert len(preview) <= 100
    assert preview.endswith("...")


def test_extract_stock_info_us_ticker():
    """US ticker extraction (ASCII symbol)."""
    msg = "AAPL earnings beat (+3%)"
    code, name = extract_stock_info(msg)
    assert code == "AAPL"
    assert name is None


def test_extract_stock_info_none():
    """No stock info in message."""
    msg = "Broad market recap with no ticker inline"
    code, name = extract_stock_info(msg)
    assert code is None


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            print(f"  PASS: {test_fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test_fn.__name__} - {e}")
            failed += 1
    sys.exit(0 if failed == 0 else 1)
