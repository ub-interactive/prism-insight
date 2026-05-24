"""Supported report output languages for the post-analysis translation layer."""

from __future__ import annotations

from enum import Enum

# ISO 639-1 codes accepted by CLI, orchestrator, and PRISM_LANGUAGE.
SUPPORTED_OUTPUT_LANGUAGES: frozenset[str] = frozenset(
    {"en", "ja", "ko", "zh", "es", "fr", "de"}
)

LANGUAGE_DISPLAY_NAMES: dict[str, str] = {
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese (Simplified)",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}


class OutputLanguage(str, Enum):
    """Report output language codes."""

    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"
    CHINESE = "zh"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"


def normalize_output_language(code: str | None, *, default: str = "en") -> str:
    """Normalize a language code; unknown values fall back to *default*."""
    if not code:
        return default
    normalized = code.strip().lower().replace("_", "-").split("-")[0]
    if normalized in SUPPORTED_OUTPUT_LANGUAGES:
        return normalized
    return default


def get_language_display_name(code: str) -> str:
    """Human-readable language name for prompts and logging."""
    normalized = normalize_output_language(code)
    return LANGUAGE_DISPLAY_NAMES.get(normalized, normalized.upper())


def needs_translation(target_language: str) -> bool:
    """True when the English report should pass through the translator."""
    return normalize_output_language(target_language) != "en"
