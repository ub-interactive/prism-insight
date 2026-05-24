"""LLM-backed translator agent for English analysis reports."""

from __future__ import annotations

import logging
import re
from typing import Optional

from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from prism.core.config.models import get_configured_model, get_optional_reasoning_effort
from prism.core.openai.error_logging import log_openai_error
from prism.reporting.translation.languages import get_language_display_name

logger = logging.getLogger(__name__)

TRANSLATION_MODEL = get_configured_model("us_translation", "gpt-5-nano")

# Roughly 12k tokens of markdown per chunk (conservative for long reports).
_MAX_CHUNK_CHARS = 48_000


def _build_translator_instruction(target_language: str) -> str:
    language_name = get_language_display_name(target_language)
    return f"""You are a professional financial report translator for PRISM-INSIGHT.

Translate the user's English stock analysis markdown into {language_name}.

Rules:
1. Preserve all Markdown structure (# headings, **bold**, lists, tables, horizontal rules).
2. Do NOT translate or alter: stock tickers (e.g. AAPL), numeric values, dates in YYYY.MM.DD form,
   HTML blocks (including chart `<div>` sections), URLs, or JSON-like fragments.
3. Keep company legal names in English when there is no widely used local name; otherwise use the
   standard local market name.
4. Use formal, investor-facing tone appropriate for {language_name}.
5. Output ONLY the translated markdown — no preamble, no code fences wrapping the whole document.
"""


def _split_markdown_for_translation(markdown: str) -> list[str]:
    """Split long reports on section breaks while keeping HTML chart blocks intact."""
    if len(markdown) <= _MAX_CHUNK_CHARS:
        return [markdown]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for part in re.split(r"(\n---\n)", markdown):
        part_len = len(part)
        if current and current_len + part_len > _MAX_CHUNK_CHARS:
            chunks.append("".join(current))
            current = [part]
            current_len = part_len
        else:
            current.append(part)
            current_len += part_len

    if current:
        chunks.append("".join(current))

    return chunks or [markdown]


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=8, max=24),
    retry=retry_if_exception_type(Exception),
)
async def _translate_chunk(
    chunk: str,
    target_language: str,
    *,
    chunk_index: int,
    chunk_total: int,
) -> str:
    language_name = get_language_display_name(target_language)
    agent = Agent(
        name="report_translator_agent",
        instruction=_build_translator_instruction(target_language),
    )
    llm = await agent.attach_llm(OpenAIAugmentedLLM)

    part_note = ""
    if chunk_total > 1:
        part_note = f"\n(This is part {chunk_index + 1} of {chunk_total} of one report; keep continuity.)"

    message = f"""Translate the following English investment analysis markdown to {language_name}.
{part_note}

--- BEGIN MARKDOWN ---
{chunk}
--- END MARKDOWN ---
"""

    return await llm.generate_str(
        message=message,
        request_params=RequestParams(
            model=TRANSLATION_MODEL,
            maxTokens=32000,
            max_iterations=1,
            parallel_tool_calls=False,
            use_history=False,
            **get_optional_reasoning_effort(TRANSLATION_MODEL, "none"),
        ),
    )


async def translate_report_markdown(
    english_markdown: str,
    target_language: str,
    *,
    log: Optional[logging.Logger] = None,
) -> str:
    """
    Translate a completed English report to *target_language*.

    Returns the original markdown when *target_language* is English or input is empty.
    """
    active_logger = log or logger
    text = (english_markdown or "").strip()
    if not text:
        return english_markdown

    language_name = get_language_display_name(target_language)
    chunks = _split_markdown_for_translation(text)
    active_logger.info(
        "Translating report to %s (%d chunk(s), %d characters)",
        language_name,
        len(chunks),
        len(text),
    )

    translated_parts: list[str] = []
    try:
        for index, chunk in enumerate(chunks):
            translated = await _translate_chunk(
                chunk,
                target_language,
                chunk_index=index,
                chunk_total=len(chunks),
            )
            translated_parts.append(translated.strip())
    except Exception as exc:
        log_openai_error(active_logger, exc, f"report translation to {language_name}")
        raise

    result = "\n".join(translated_parts).strip()
    active_logger.info("Report translation complete — %d characters", len(result))
    return result
