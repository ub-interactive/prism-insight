"""Regression tests for gh #263 — duplicate investing warning Firecrawl-style handlers historically appended a canonical disclaimer block; stripping must remain deterministic.

Firecrawl-style handlers historically appended a canonical disclaimer block; stripping must remain deterministic.
English disclaimer. The LLM frequently appends its own investment-warning line
on top, producing two near-identical disclaimers.
`cores.disclaimer_utils.strip_trailing_disclaimer` removes the LLM-emitted block
before the canonical one is appended.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cores.disclaimer_utils import strip_trailing_disclaimer as _strip


# --- Cases that MUST be stripped (the gh #263 reproductions) ----------------

def test_strips_en_informational_suffix():
    body = (
        "AI datacenter themes look extended.\n"
        "Top names: NVDA, AVGO, MRVL"
    )
    text = (
        body
        + "\n\n⚠️ This material is for informational purposes only."
        + " Investing is at your own risk."
    )
    assert _strip(text) == body


def test_strips_en_duplicate_reference_like_canonical():
    body = "Bio theme scan complete..."
    text = (
        body
        + "\n\n⚠️ For informational purposes only. Investment decisions are your own responsibility."
    )
    assert _strip(text) == body


def test_strips_en_responsibility_line():
    body = "Theme temperature: cool"
    text = body + "\n⚠️ You alone are responsible for investment decisions."
    assert _strip(text) == body


def test_strips_en_phrasing_alt():
    body = "Theme temperature: warming"
    text = (
        body
        + "\n\n⚠️ This content is educational only."
        + " Investing involves risk."
    )
    assert _strip(text) == body


def test_strips_not_financial_advice():
    body = "Bullet 1\nBullet 2"
    text = body + "\n\n⚠️ This is not financial advice."
    assert _strip(text) == body


def test_strips_multiple_trailing_warning_lines():
    body = "Main thesis text."
    text = (
        body
        + "\n\n⚠️ Nothing here is personalized investment advice."
        + "\n⚠️ Investing remains your sole responsibility."
    )
    assert _strip(text) == body


def test_handles_trailing_whitespace():
    body = "Lead paragraph"
    text = body + "\n\n⚠️ For informational purposes only. Not financial advice.\n   \n"
    assert _strip(text) == body


# --- Cases that MUST be preserved -------------------------------------------

def test_preserves_warning_in_middle_of_body():
    """A ⚠️ inside the body must not be stripped."""
    text = (
        "1. Temperature: elevated\n"
        "⚠️ Short-term pullback risk flagged.\n"
        "2. Leaders: NVDA"
    )
    assert _strip(text) == text


def test_preserves_text_without_warning():
    text = "Theme scan finished.\nTop tickers listed above."
    assert _strip(text) == text


def test_preserves_unrelated_warning_at_end():
    """A trailing ⚠️ that is not investment-related must be preserved."""
    text = "Done.\n\n⚠️ Data note: liquidity may vary by venue."
    assert _strip(text) == text


def test_preserves_empty_string():
    assert _strip("") == ""


def test_preserves_none_safely():
    assert _strip(None) is None
