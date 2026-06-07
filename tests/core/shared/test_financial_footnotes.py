import pytest
from unittest.mock import AsyncMock, patch

from prism.core.shared.footnotes import (
    TermFootnote,
    _coerce_terms,
    annotate_financial_terms,
    insert_footnote_markers,
)


def test_insert_footnotes_first_occurrence_only_and_document_order():
    report = (
        "# Report\n\n"
        "Free cash flow improved while the P/E ratio contracted.\n\n"
        "Later, free cash flow was mentioned again and P/E ratio appeared again."
    )
    terms = [
        TermFootnote(
            term="P/E ratio",
            surface_form="P/E ratio",
            definition="The price-to-earnings ratio compares a company's share price with its earnings per share.",
        ),
        TermFootnote(
            term="free cash flow",
            surface_form="free cash flow",
            definition="Free cash flow is cash generated after operating expenses and capital spending.",
        ),
    ]

    result = insert_footnote_markers(report, terms)

    assert "Free cash flow[^1] improved while the P/E ratio[^2] contracted." in result
    assert "Later, free cash flow was mentioned again and P/E ratio appeared again." in result
    assert result.count("free cash flow[^") == 0
    assert result.count("P/E ratio[^") == 1
    assert "[^1]: Free cash flow is cash generated after operating expenses and capital spending." in result
    assert "[^2]: The price-to-earnings ratio compares a company's share price with its earnings per share." in result


def test_insert_footnotes_deduplicates_terms_by_surface_form():
    report = "Revenue grew, and revenue quality improved."
    terms = [
        TermFootnote(term="revenue", surface_form="Revenue", definition="Revenue is total sales before expenses."),
        TermFootnote(term="Revenue", surface_form="Revenue", definition="Duplicate definition should not be used."),
    ]

    result = insert_footnote_markers(report, terms)

    assert result.count("Revenue[^1]") == 1
    assert "Duplicate definition should not be used" not in result
    assert "[^1]: Revenue is total sales before expenses." in result


def test_insert_footnotes_prefers_longer_overlapping_match():
    report = "Free cash flow improved after cash conversion improved."
    terms = [
        TermFootnote(
            term="cash",
            surface_form="cash",
            definition="Cash is money available to a company.",
        ),
        TermFootnote(
            term="free cash flow",
            surface_form="free cash flow",
            definition="Free cash flow is cash generated after operating expenses and capital spending.",
        ),
    ]

    result = insert_footnote_markers(report, terms)

    assert "Free cash flow[^1] improved after cash[^2] conversion improved." in result
    assert "flo[^2]w" not in result
    assert "[^1]: Free cash flow is cash generated after operating expenses and capital spending." in result
    assert "[^2]: Cash is money available to a company." in result


def test_insert_footnotes_returns_original_when_no_terms_match():
    report = "Revenue improved."
    terms = [TermFootnote(term="EBITDA", surface_form="EBITDA", definition="Earnings before interest, taxes, depreciation, and amortization.")]

    result = insert_footnote_markers(report, terms)

    assert result == report


def test_insert_footnotes_skips_tables_code_blocks_and_existing_definitions():
    report = (
        "| Metric | Value |\n"
        "| --- | --- |\n"
        "| EBITDA | 100 |\n\n"
        "```text\n"
        "EBITDA appears in a code block.\n"
        "```\n\n"
        "EBITDA improved in operating results.\n\n"
        "[^9]: EBITDA old definition."
    )
    terms = [
        TermFootnote(
            term="EBITDA",
            surface_form="EBITDA",
            definition="EBITDA is earnings before interest, taxes, depreciation, and amortization.",
        )
    ]

    result = insert_footnote_markers(report, terms)

    assert "| EBITDA | 100 |" in result
    assert "EBITDA appears in a code block." in result
    assert "EBITDA[^1] improved in operating results." in result
    assert "[^9]: EBITDA old definition." in result
    assert "[^1]: EBITDA is earnings before interest, taxes, depreciation, and amortization." in result


def test_coerce_terms_accepts_valid_payload_and_filters_invalid_items():
    payload = {
        "terms": [
            {
                "term": "Free cash flow",
                "surface_form": "free cash flow",
                "definition": "Cash left after operating expenses and capital expenditures.",
            },
            {"term": "Bad", "surface_form": "", "definition": "Missing surface form."},
            "not a dictionary",
        ]
    }

    terms = _coerce_terms(payload)

    assert terms == [
        TermFootnote(
            term="Free cash flow",
            surface_form="free cash flow",
            definition="Cash left after operating expenses and capital expenditures.",
        )
    ]


@pytest.mark.asyncio
@patch("prism.core.shared.footnotes._extract_financial_terms", new_callable=AsyncMock)
async def test_annotate_financial_terms_returns_original_when_extraction_fails(mock_extract):
    mock_extract.side_effect = RuntimeError("model unavailable")
    report = "The P/E ratio contracted."

    result = await annotate_financial_terms(report, "en", logger=None)

    assert result == report


@pytest.mark.asyncio
@patch("prism.core.shared.footnotes._extract_financial_terms", new_callable=AsyncMock)
async def test_annotate_financial_terms_restores_charts(mock_extract):
    mock_extract.return_value = [
        TermFootnote(
            term="P/E ratio",
            surface_form="P/E ratio",
            definition="The price-to-earnings ratio compares price with earnings.",
        )
    ]
    report = (
        "# Report\n"
        '<img src="data:image/png;base64,chartbytes" />\n\n'
        "The P/E ratio contracted."
    )

    result = await annotate_financial_terms(report, "en", logger=None)

    assert '<img src="data:image/png;base64,chartbytes" />' in result
    assert "The P/E ratio[^1] contracted." in result
    assert "[^1]: The price-to-earnings ratio compares price with earnings." in result
