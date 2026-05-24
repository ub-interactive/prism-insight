"""Post-processing output layer: English analysis → localized report."""

from __future__ import annotations

import logging
from typing import Optional

from prism.reporting.translation.languages import needs_translation, normalize_output_language
from prism.reporting.translation.translator import translate_report_markdown

logger = logging.getLogger(__name__)


async def apply_report_output_language(
    english_markdown: str,
    target_language: str,
    *,
    log: Optional[logging.Logger] = None,
) -> str:
    """
    Apply the reporting output layer.

    Analysis agents always produce English; when *target_language* is not English,
    a dedicated translator agent localizes the final markdown.
    """
    active_logger = log or logger
    normalized = normalize_output_language(target_language)

    if not needs_translation(normalized):
        return english_markdown

    active_logger.info("Applying report output translation layer (target=%s)", normalized)
    return await translate_report_markdown(
        english_markdown,
        normalized,
        log=active_logger,
    )
