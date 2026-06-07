"""Financial term footnotes for generated reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

from prism.core.shared.config.models import get_configured_model, get_optional_reasoning_effort
from prism.core.shared.translation import extract_and_replace_charts, restore_charts
from prism.core.shared.utils import parse_llm_json

FINANCIAL_FOOTNOTE_MODEL = get_configured_model("financial_footnotes", "gpt-5.4-mini")


@dataclass(frozen=True)
class TermFootnote:
    """A financial term and its plain-language explanation."""

    term: str
    surface_form: str
    definition: str


def _normalize_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def _clean_definition(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip())
    return cleaned.rstrip(".") + "." if cleaned else ""


def _protected_spans(text: str) -> list[tuple[int, int]]:
    """Return spans where footnote markers should not be inserted."""
    spans: list[tuple[int, int]] = []

    for match in re.finditer(r"```[\s\S]*?```", text):
        spans.append(match.span())

    for match in re.finditer(r"(?m)^\[\^[^\]]+\]:.*$", text):
        spans.append(match.span())

    for match in re.finditer(r"(?m)^\|.*\|$", text):
        spans.append(match.span())

    return sorted(spans)


def _inside_spans(index: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= index < end for start, end in spans)


def _spans_overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def _find_next_unprotected_non_overlapping(
    text: str,
    surface_form: str,
    protected_spans: list[tuple[int, int]],
    occupied_spans: list[tuple[int, int]],
) -> tuple[int, int] | None:
    if not surface_form:
        return None

    pattern = re.compile(re.escape(surface_form), re.IGNORECASE)
    search_from = 0
    while True:
        match = pattern.search(text, search_from)
        if match is None:
            return None
        span = (match.start(), match.end())
        if _inside_spans(match.start(), protected_spans):
            search_from = match.end()
            continue
        if any(_spans_overlap(span, occupied) for occupied in occupied_spans):
            search_from = match.end()
            continue
        return span


def insert_footnote_markers(report_md: str, terms: list[TermFootnote]) -> str:
    """Insert markdown footnote markers at each term's first occurrence."""
    if not report_md.strip() or not terms:
        return report_md

    protected_spans = _protected_spans(report_md)
    seen: set[str] = set()
    pending_terms: list[TermFootnote] = []

    for term in terms:
        surface = term.surface_form.strip()
        definition = _clean_definition(term.definition)
        key = _normalize_key(surface)
        if not surface or not definition or key in seen:
            continue
        seen.add(key)
        pending_terms.append(TermFootnote(term.term.strip(), surface, definition))

    pending_terms.sort(key=lambda term: len(term.surface_form), reverse=True)
    occupied_spans: list[tuple[int, int]] = []
    candidates: list[tuple[int, int, TermFootnote]] = []

    for term in pending_terms:
        match_span = _find_next_unprotected_non_overlapping(
            report_md, term.surface_form, protected_spans, occupied_spans
        )
        if match_span is not None:
            start, end = match_span
            occupied_spans.append(match_span)
            candidates.append((start, end, term))

    if not candidates:
        return report_md

    candidates.sort(key=lambda item: item[0])
    output = report_md
    offset = 0
    definitions: list[str] = []

    for number, (_index, end, term) in enumerate(candidates, start=1):
        insert_at = end + offset
        marker = f"[^{number}]"
        output = output[:insert_at] + marker + output[insert_at:]
        offset += len(marker)
        definitions.append(f"[^{number}]: {term.definition}")

    return output.rstrip() + "\n\n---\n\n## Footnotes\n\n" + "\n".join(definitions) + "\n"


def _coerce_terms(payload: dict[str, Any] | None) -> list[TermFootnote]:
    """Validate parsed LLM JSON into TermFootnote objects."""
    if not isinstance(payload, dict):
        return []

    raw_terms = payload.get("terms")
    if not isinstance(raw_terms, list):
        return []

    terms: list[TermFootnote] = []
    for item in raw_terms:
        if not isinstance(item, dict):
            continue
        term = str(item.get("term", "")).strip()
        surface_form = str(item.get("surface_form", "")).strip()
        definition = str(item.get("definition", "")).strip()
        if term and surface_form and definition:
            terms.append(TermFootnote(term=term, surface_form=surface_form, definition=definition))

    return terms


async def _extract_financial_terms(report_md: str, language: str) -> list[TermFootnote]:
    """Ask an LLM to identify financial terms and plain-language definitions."""
    agent = Agent(
        name="financial_footnote_extractor",
        instruction=(
            "You identify financial terms in investment research reports. "
            "Return only strict JSON. Do not rewrite the report."
        ),
        server_names=[],
    )
    llm = await agent.attach_llm(OpenAIAugmentedLLM)

    message = f"""Identify financial terms in this investment report that a general individual investor may not understand.

Return strict JSON with this exact shape:
{{
  "terms": [
    {{
      "term": "canonical term name",
      "surface_form": "exact substring as it appears in the report",
      "definition": "one concise plain-language definition in English"
    }}
  ]
}}

Rules:
- Include financial, accounting, valuation, trading, macroeconomic, and market-structure terms.
- Use the exact first visible report substring for surface_form, preserving capitalization and punctuation.
- Definitions must be one sentence, clear enough for retail investors, and not investment advice.
- Do not include company names, ticker symbols, dates, plain percentages, or ordinary words.
- Do not include terms that appear only in markdown tables, code blocks, chart placeholders, or existing footnote definitions.
- The report language parameter is "{language}", but this extraction pass receives the pre-translation English report; write definitions in English.
- Output only JSON. No markdown fence.

Report:
{report_md}
"""

    response = await llm.generate_str(
        message=message,
        request_params=RequestParams(
            model=FINANCIAL_FOOTNOTE_MODEL,
            maxTokens=8000,
            max_iterations=1,
            parallel_tool_calls=False,
            use_history=False,
            **get_optional_reasoning_effort(FINANCIAL_FOOTNOTE_MODEL, "none"),
        ),
    )
    payload = parse_llm_json(response, "financial footnote extraction")
    return _coerce_terms(payload)


async def annotate_financial_terms(report_md: str, language: str, logger) -> str:
    """Annotate financial terms with markdown footnotes, returning original markdown on failure."""
    if not report_md or not report_md.strip():
        return report_md

    try:
        processed_report, charts = extract_and_replace_charts(report_md)
        terms = await _extract_financial_terms(processed_report, language)
        if not terms:
            return report_md

        annotated = insert_footnote_markers(processed_report, terms)
        return restore_charts(annotated, charts)
    except Exception as exc:
        if logger:
            logger.warning(f"Financial footnote annotation skipped: {exc}")
        return report_md
