"""Financial term footnotes for generated reports."""

from __future__ import annotations

from dataclasses import dataclass
import re


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
