import pytest
from unittest.mock import AsyncMock, MagicMock

from prism.core.shared.analysis_helpers import (
    SEQUENTIAL_DATA_SECTIONS,
    add_strategy_and_summary,
    clean_summary_text,
    finalize_markdown,
)


def test_sequential_sections_constant():
    assert "price_volume_analysis" in SEQUENTIAL_DATA_SECTIONS
    assert len(SEQUENTIAL_DATA_SECTIONS) == 5


def test_clean_summary_text_strips_duplicate_title():
    raw = "# Apple Inc. (AAPL) Analysis Report\n\n**Publication Date:** 2026.06.06\n\nBody"
    cleaned = clean_summary_text(raw, company_name="Apple Inc.", display_symbol="AAPL")
    assert "Apple Inc." not in cleaned.split("Body")[0]
    assert "Body" in cleaned


@pytest.mark.asyncio
async def test_finalize_markdown_english_skips_translation(monkeypatch):
    monkeypatch.setattr(
        "prism.core.shared.analysis_helpers.annotate_financial_terms",
        AsyncMock(return_value="annotated"),
    )
    logger = MagicMock()
    result = await finalize_markdown(logger, "# Report\n", language="en", market="us")
    assert result == "annotated"


@pytest.mark.asyncio
async def test_add_strategy_and_summary_adds_keys(monkeypatch):
    async def fake_strategy(*args, **kwargs):
        return "strategy text"

    async def fake_summary(*args, **kwargs):
        return "summary text"

    monkeypatch.setattr(
        "prism.core.shared.analysis_helpers.generate_investment_strategy",
        fake_strategy,
    )
    monkeypatch.setattr(
        "prism.core.shared.analysis_helpers.generate_summary",
        fake_summary,
    )
    logger = MagicMock()
    sections = {"price_volume_analysis": "pv"}
    out = await add_strategy_and_summary(
        logger,
        sections,
        company_name="Apple Inc.",
        display_symbol="AAPL",
        reference_date="20260606",
        language="en",
    )
    assert "investment_strategy" in out
    assert "summary" in out
