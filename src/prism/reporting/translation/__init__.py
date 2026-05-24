"""Report output translation (English pipeline → localized markdown)."""

from prism.reporting.translation.languages import (
    LANGUAGE_DISPLAY_NAMES,
    SUPPORTED_OUTPUT_LANGUAGES,
    OutputLanguage,
    get_language_display_name,
    needs_translation,
    normalize_output_language,
)
from prism.reporting.translation.output_layer import apply_report_output_language
from prism.reporting.translation.translator import translate_report_markdown

__all__ = [
    "LANGUAGE_DISPLAY_NAMES",
    "SUPPORTED_OUTPUT_LANGUAGES",
    "OutputLanguage",
    "apply_report_output_language",
    "get_language_display_name",
    "needs_translation",
    "normalize_output_language",
    "translate_report_markdown",
]
