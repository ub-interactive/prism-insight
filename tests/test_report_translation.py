"""Tests for the report translation output layer."""

import pytest

from prism.reporting.translation.languages import (
    get_language_display_name,
    needs_translation,
    normalize_output_language,
)
from prism.reporting.translation.output_layer import apply_report_output_language


class TestLanguageNormalization:
    def test_english_default(self):
        assert normalize_output_language(None) == "en"
        assert normalize_output_language("") == "en"

    def test_locale_suffix_stripped(self):
        assert normalize_output_language("ja-JP") == "ja"

    def test_unknown_falls_back_to_english(self):
        assert normalize_output_language("xx") == "en"

    def test_needs_translation(self):
        assert needs_translation("en") is False
        assert needs_translation("ko") is True

    def test_display_name(self):
        assert get_language_display_name("ko") == "Korean"


@pytest.mark.asyncio
async def test_output_layer_skips_english(monkeypatch):
    called = False

    async def fake_translate(*_args, **_kwargs):
        nonlocal called
        called = True
        return "translated"

    monkeypatch.setattr(
        "prism.reporting.translation.output_layer.translate_report_markdown",
        fake_translate,
    )

    source = "# Report\n\nEnglish body."
    result = await apply_report_output_language(source, "en")
    assert result == source
    assert called is False


@pytest.mark.asyncio
async def test_output_layer_invokes_translator(monkeypatch):
    async def fake_translate(markdown, target_language, **kwargs):
        assert target_language == "ja"
        assert "English body" in markdown
        return "日本語レポート"

    monkeypatch.setattr(
        "prism.reporting.translation.output_layer.translate_report_markdown",
        fake_translate,
    )

    result = await apply_report_output_language("# Report\n\nEnglish body.", "ja")
    assert result == "日本語レポート"
