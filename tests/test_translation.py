import pytest
from unittest.mock import AsyncMock, patch

from prism.core.translation import (
    extract_and_replace_charts,
    restore_charts,
    translate_report,
    translate_text,
)


def test_extract_and_replace_charts():
    # Standalone img tag
    text_standalone = (
        "Some text before\n"
        '<img src="data:image/jpeg;base64,abcdef123456" alt="Test Chart" width="900" />\n'
        "Some text after"
    )
    processed, charts = extract_and_replace_charts(text_standalone)
    assert "<!-- CHART_PLACEHOLDER_0 -->" in processed
    assert '<img src="data:image/jpeg;base64,abcdef123456"' not in processed
    assert len(charts) == 1
    assert list(charts.keys())[0] == "<!-- CHART_PLACEHOLDER_0 -->"
    assert "abcdef123456" in charts["<!-- CHART_PLACEHOLDER_0 -->"]

    # Div wrapped img tag
    text_div = (
        "Before\n"
        '<div style="text-align: center;">\n'
        '  <img src="data:image/png;base64,pngdata" alt="Another Chart" width="800" />\n'
        '</div>\n'
        "After"
    )
    processed_div, charts_div = extract_and_replace_charts(text_div)
    assert "<!-- CHART_PLACEHOLDER_0 -->" in processed_div
    assert '<div style="text-align: center;">' not in processed_div
    assert len(charts_div) == 1
    assert "pngdata" in charts_div["<!-- CHART_PLACEHOLDER_0 -->"]


def test_restore_charts():
    text = "Intro\n<!-- CHART_PLACEHOLDER_0 -->\nOutro"
    charts = {"<!-- CHART_PLACEHOLDER_0 -->": '<img src="data:image/png;base64,xyz" />'}
    restored = restore_charts(text, charts)
    assert restored == "Intro\n<img src=\"data:image/png;base64,xyz\" />\nOutro"


@pytest.mark.asyncio
async def test_translate_report_no_translation_for_english():
    report = "# Apple Report\n## Section 1\nSome info"
    result = await translate_report(report, "en")
    assert result == report

    result_none = await translate_report(report, None)
    assert result_none == report

    result_empty = await translate_report(report, "")
    assert result_empty == report


@pytest.mark.asyncio
@patch("mcp_agent.workflows.llm.augmented_llm_openai.OpenAIAugmentedLLM.generate_str", new_callable=AsyncMock)
async def test_translate_text(mock_generate_str):
    mock_generate_str.return_value = "Mock translated response text"
    
    translated = await translate_text("Original text here", "ko")
    
    assert translated == "Mock translated response text"
    mock_generate_str.assert_called_once()
    
    # Check that prompt contains target language name (Korean)
    call_args = mock_generate_str.call_args[1]
    assert "Korean" in call_args["message"]
    assert "Original text here" in call_args["message"]


@pytest.mark.asyncio
@patch("mcp_agent.workflows.llm.augmented_llm_openai.OpenAIAugmentedLLM.generate_str", new_callable=AsyncMock)
async def test_translate_report_end_to_end(mock_generate_str):
    # Setup mock translations for each segment
    # Segment 1: Header/Intro (before H2)
    # Segment 2: Section 1
    # Segment 3: Section 2
    mock_generate_str.side_effect = [
        "# Mocked Header\n<!-- CHART_PLACEHOLDER_0 -->",
        "## Mocked Section 1\nContent 1",
        "## Mocked Section 2\nContent 2"
    ]

    report = (
        "# Apple Report\n"
        '<img src="data:image/jpeg;base64,chartbytes" />\n'
        "## Section 1\n"
        "Original Content 1\n"
        "## Section 2\n"
        "Original Content 2"
    )

    translated_report = await translate_report(report, "zh")

    # Assert that charts are restored correctly and mock calls are made
    assert "# Mocked Header" in translated_report
    assert "## Mocked Section 1\nContent 1" in translated_report
    assert "## Mocked Section 2\nContent 2" in translated_report
    assert '<img src="data:image/jpeg;base64,chartbytes" />' in translated_report
    assert mock_generate_str.call_count == 3
