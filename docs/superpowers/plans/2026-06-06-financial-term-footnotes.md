# Financial Term Footnotes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add markdown footnotes that explain financial terms in both US and CN generated reports, using an LLM extraction pass and deterministic marker insertion.

**Architecture:** The report body remains unchanged except for footnote markers inserted by Python. A new `prism.core.footnotes` module asks an LLM for structured term definitions, inserts `[^n]` markers at each term's first occurrence, appends markdown footnote definitions, and gracefully returns the original report on failure. Both US and CN report pipelines call this after `clean_markdown()` and before optional translation; translation prompts are updated to preserve footnote marker syntax.

**Tech Stack:** Python 3.13, `mcp_agent` `Agent`, `OpenAIAugmentedLLM`, `RequestParams`, existing `parse_llm_json`, `pytest`, `pytest.mark.asyncio`, Python-Markdown footnote support already enabled through `markdown.extensions.extra`.

---

## Scope

Implement footnotes for generated report markdown only. Do not change trading, data prefetch, analyst prompts, PDF conversion, or report save paths. The footnote pass is best-effort: errors never block report generation.

## File Structure

- Create: `src/prism/core/footnotes.py`
  - Owns financial term extraction, response validation, deterministic first-occurrence marker insertion, and graceful fallback.
  - Public API: `annotate_financial_terms(report_md: str, language: str, logger) -> str`.
- Create: `tests/test_financial_footnotes.py`
  - Unit tests for marker insertion, protected regions, LLM response parsing, graceful fallback, and chart restoration.
- Modify: `src/prism/core/analysis.py`
  - Calls `annotate_financial_terms()` in the US report path after `clean_markdown()` and before `translate_report()`.
- Modify: `src/prism/core/analysis_cn.py`
  - Calls `annotate_financial_terms()` in the CN report path after `clean_markdown()` and before `translate_report()`.
- Modify: `src/prism/core/translation.py`
  - Adds prompt instructions to preserve `[^1]` markers and `[^1]:` labels exactly while translating footnote definitions.
- Modify: `tests/test_translation.py`
  - Verifies translation prompts explicitly preserve markdown footnote syntax.

---

### Task 1: Add Pure Footnote Insertion Helpers

**Files:**
- Create: `src/prism/core/footnotes.py`
- Test: `tests/test_financial_footnotes.py`

- [ ] **Step 1: Write failing tests for deterministic first-occurrence insertion**

Create `tests/test_financial_footnotes.py` with these tests:

```python
from prism.core.footnotes import TermFootnote, insert_footnote_markers


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/test_financial_footnotes.py -q
```

Expected: import failure similar to `ModuleNotFoundError: No module named 'prism.core.footnotes'`.

- [ ] **Step 3: Create `src/prism/core/footnotes.py` with minimal pure helpers**

Create `src/prism/core/footnotes.py`:

```python
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


def _find_first_unprotected(text: str, surface_form: str, spans: list[tuple[int, int]]) -> int | None:
    if not surface_form:
        return None

    search_from = 0
    while True:
        idx = text.find(surface_form, search_from)
        if idx == -1:
            return None
        if not _inside_spans(idx, spans):
            return idx
        search_from = idx + len(surface_form)


def insert_footnote_markers(report_md: str, terms: list[TermFootnote]) -> str:
    """Insert markdown footnote markers at each term's first occurrence."""
    if not report_md.strip() or not terms:
        return report_md

    spans = _protected_spans(report_md)
    seen: set[str] = set()
    candidates: list[tuple[int, TermFootnote]] = []

    for term in terms:
        surface = term.surface_form.strip()
        definition = _clean_definition(term.definition)
        key = _normalize_key(surface)
        if not surface or not definition or key in seen:
            continue
        seen.add(key)
        index = _find_first_unprotected(report_md, surface, spans)
        if index is not None:
            candidates.append((index, TermFootnote(term.term.strip(), surface, definition)))

    if not candidates:
        return report_md

    candidates.sort(key=lambda item: item[0])
    output = report_md
    offset = 0
    definitions: list[str] = []

    for number, (index, term) in enumerate(candidates, start=1):
        insert_at = index + offset + len(term.surface_form)
        marker = f"[^{number}]"
        output = output[:insert_at] + marker + output[insert_at:]
        offset += len(marker)
        definitions.append(f"[^{number}]: {term.definition}")

    return output.rstrip() + "\n\n---\n\n## Footnotes\n\n" + "\n".join(definitions) + "\n"
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest tests/test_financial_footnotes.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/prism/core/footnotes.py tests/test_financial_footnotes.py
git commit -m "feat: add financial footnote insertion helpers"
```

---

### Task 2: Protect Tables, Code Blocks, and Existing Footnotes

**Files:**
- Modify: `tests/test_financial_footnotes.py`
- Modify: `src/prism/core/footnotes.py`

- [ ] **Step 1: Add failing tests for protected regions**

Append these tests to `tests/test_financial_footnotes.py`:

```python
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
```

- [ ] **Step 2: Run the targeted test**

Run:

```bash
pytest tests/test_financial_footnotes.py::test_insert_footnotes_skips_tables_code_blocks_and_existing_definitions -q
```

Expected: PASS if Task 1 already included the protected span code. If it passes, keep this task as a test-coverage commit. If it fails, update `_protected_spans()` exactly as shown in Task 1 Step 3.

- [ ] **Step 3: Run all footnote tests**

Run:

```bash
pytest tests/test_financial_footnotes.py -q
```

Expected: `3 passed`.

- [ ] **Step 4: Commit**

```bash
git add src/prism/core/footnotes.py tests/test_financial_footnotes.py
git commit -m "test: cover protected footnote regions"
```

---

### Task 3: Add LLM Term Extraction With Graceful Fallback

**Files:**
- Modify: `src/prism/core/footnotes.py`
- Modify: `tests/test_financial_footnotes.py`

- [ ] **Step 1: Add failing tests for JSON coercion and graceful annotation**

Append these tests:

```python
import pytest
from unittest.mock import AsyncMock, patch

from prism.core.footnotes import (
    TermFootnote,
    _coerce_terms,
    annotate_financial_terms,
    insert_footnote_markers,
)


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
@patch("prism.core.footnotes._extract_financial_terms", new_callable=AsyncMock)
async def test_annotate_financial_terms_returns_original_when_extraction_fails(mock_extract):
    mock_extract.side_effect = RuntimeError("model unavailable")
    report = "The P/E ratio contracted."

    result = await annotate_financial_terms(report, "en", logger=None)

    assert result == report


@pytest.mark.asyncio
@patch("prism.core.footnotes._extract_financial_terms", new_callable=AsyncMock)
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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
pytest tests/test_financial_footnotes.py -q
```

Expected: failures for missing `_coerce_terms`, `_extract_financial_terms`, or `annotate_financial_terms`.

- [ ] **Step 3: Implement LLM extraction and graceful wrapper**

Update `src/prism/core/footnotes.py` by adding these imports near the top:

```python
from typing import Any

from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

from prism.core.config.models import get_configured_model, get_optional_reasoning_effort
from prism.core.translation import extract_and_replace_charts, restore_charts
from prism.core.utils import parse_llm_json
```

Add this constant below the imports:

```python
FINANCIAL_FOOTNOTE_MODEL = get_configured_model("financial_footnotes", "gpt-5.4-mini")
```

Append these functions after `insert_footnote_markers()`:

```python
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
```

- [ ] **Step 4: Run footnote tests**

Run:

```bash
pytest tests/test_financial_footnotes.py -q
```

Expected: all footnote tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/prism/core/footnotes.py tests/test_financial_footnotes.py
git commit -m "feat: extract financial terms for report footnotes"
```

---

### Task 4: Add Footnote Annotation to US and CN Report Pipelines

**Files:**
- Modify: `src/prism/core/analysis.py`
- Modify: `src/prism/core/analysis_cn.py`

- [ ] **Step 1: Modify US imports**

In `src/prism/core/analysis.py`, add this import with the other `prism.core` imports:

```python
from prism.core.footnotes import annotate_financial_terms
```

- [ ] **Step 2: Call annotation in the US pipeline**

Replace this block:

```python
        # 11. Clean up markdown formatting
        final_report = clean_markdown(final_report)

        if language and language.lower() != "en":
            from prism.core.translation import translate_report
            final_report = await translate_report(final_report, language)
```

with:

```python
        # 11. Clean up markdown formatting
        final_report = clean_markdown(final_report)
        final_report = await annotate_financial_terms(final_report, language, logger)

        if language and language.lower() != "en":
            from prism.core.translation import translate_report
            final_report = await translate_report(final_report, language)
```

- [ ] **Step 3: Modify CN imports**

In `src/prism/core/analysis_cn.py`, add:

```python
from prism.core.footnotes import annotate_financial_terms
```

- [ ] **Step 4: Call annotation in the CN pipeline**

Replace this block:

```python
        final_report = clean_markdown(final_report)

        if language and language.lower() != "en":
            from prism.core.translation import translate_report

            final_report = await translate_report(final_report, language)
```

with:

```python
        final_report = clean_markdown(final_report)
        final_report = await annotate_financial_terms(final_report, language, logger)

        if language and language.lower() != "en":
            from prism.core.translation import translate_report

            final_report = await translate_report(final_report, language)
```

- [ ] **Step 5: Run import smoke tests**

Run:

```bash
python -m py_compile src/prism/core/footnotes.py src/prism/core/analysis.py src/prism/core/analysis_cn.py
```

Expected: no output and exit code 0.

- [ ] **Step 6: Run focused tests**

Run:

```bash
pytest tests/test_financial_footnotes.py tests/test_cn_report_generation.py -q
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/prism/core/analysis.py src/prism/core/analysis_cn.py
git commit -m "feat: annotate generated reports with financial footnotes"
```

---

### Task 5: Preserve Footnote Syntax During Translation

**Files:**
- Modify: `src/prism/core/translation.py`
- Modify: `tests/test_translation.py`

- [ ] **Step 1: Add a failing translation prompt test**

Append this test to `tests/test_translation.py`:

```python
@pytest.mark.asyncio
@patch("mcp_agent.workflows.llm.augmented_llm_openai.OpenAIAugmentedLLM.generate_str", new_callable=AsyncMock)
async def test_translate_text_preserves_footnote_syntax_instruction(mock_generate_str):
    mock_generate_str.return_value = "市盈率[^1]\n\n[^1]: 市盈率用于比较股价与每股收益。"

    await translate_text("P/E ratio[^1]\n\n[^1]: The P/E ratio compares price with earnings.", "zh")

    call_args = mock_generate_str.call_args[1]
    prompt = call_args["message"]
    assert "Preserve markdown footnote markers like [^1] exactly" in prompt
    assert "Preserve footnote definition labels like [^1]: exactly" in prompt
```

- [ ] **Step 2: Run the new test to verify it fails**

Run:

```bash
pytest tests/test_translation.py::test_translate_text_preserves_footnote_syntax_instruction -q
```

Expected: assertion failure because the prompt does not yet mention footnote marker preservation.

- [ ] **Step 3: Update translator instruction and prompt**

In `src/prism/core/translation.py`, replace the `instruction` value in `translate_text()`:

```python
        instruction=(
            "You are a professional financial translator. "
            "Translate all English text to the target language accurately and professionally. "
            "Preserve all markdown formatting, lists, bold text, tables, and HTML comments/placeholders exactly."
        ),
```

with:

```python
        instruction=(
            "You are a professional financial translator. "
            "Translate all English text to the target language accurately and professionally. "
            "Preserve all markdown formatting, lists, bold text, tables, footnote markers, "
            "footnote definition labels, and HTML comments/placeholders exactly."
        ),
```

Then replace the `prompt` construction:

```python
    prompt = (
        f"Translate the following text into standard financial terminology in {lang_name}. "
        "Preserve all markdown headers, bold text, tables, bullet points, HTML comments, and placeholders exactly as they are. "
        "Output only the translated text, with no conversational preamble, explanation, or introduction:\n\n"
        f"{text}"
    )
```

with:

```python
    prompt = (
        f"Translate the following text into standard financial terminology in {lang_name}. "
        "Preserve all markdown headers, bold text, tables, bullet points, HTML comments, and placeholders exactly as they are. "
        "Preserve markdown footnote markers like [^1] exactly. "
        "Preserve footnote definition labels like [^1]: exactly; translate only the definition text after the label. "
        "Output only the translated text, with no conversational preamble, explanation, or introduction:\n\n"
        f"{text}"
    )
```

- [ ] **Step 4: Run translation tests**

Run:

```bash
pytest tests/test_translation.py -q
```

Expected: all translation tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/prism/core/translation.py tests/test_translation.py
git commit -m "fix: preserve footnote syntax during translation"
```

---

### Task 6: Full Verification

**Files:**
- Verify only; no code changes expected.

- [ ] **Step 1: Run focused unit tests**

Run:

```bash
pytest tests/test_financial_footnotes.py tests/test_translation.py tests/test_cn_*.py -q
```

Expected: all tests pass. Existing warnings such as `PyPDF2` deprecation warnings are acceptable.

- [ ] **Step 2: Run compile check**

Run:

```bash
python -m py_compile src/prism/core/footnotes.py src/prism/core/analysis.py src/prism/core/analysis_cn.py src/prism/core/translation.py
```

Expected: no output and exit code 0.

- [ ] **Step 3: Optional live smoke test for CN report generation**

Run only if API keys and the local environment are configured:

```bash
python -m prism.ops.dev.demo 600919 --market cn --language zh
```

Expected:
- Report completes.
- Generated markdown contains translated footnote markers such as `[^1]`.
- Generated markdown contains translated footnote definitions with labels such as `[^1]:`.
- PDF conversion completes.

- [ ] **Step 4: Optional live smoke test for US report generation**

Run only if API keys and US data dependencies are configured:

```bash
python -m prism.ops.dev.demo AAPL --market us --language en
```

Expected:
- Report completes.
- Generated markdown contains financial term markers such as `[^1]`.
- Generated markdown contains a `## Footnotes` section.
- PDF conversion completes.

- [ ] **Step 5: Final status check**

Run:

```bash
git status --short --branch
```

Expected: clean working tree after all commits.

---

## Self-Review

- **Spec coverage:** The plan covers both US and CN reports, LLM-detected terms, native markdown footnotes, first occurrence only, no cap, pre-translation insertion, translation preservation, and graceful fallback.
- **Scope check:** This is one focused subsystem: report post-processing. It does not require splitting into separate plans.
- **Placeholder scan:** No implementation step relies on unspecified paths, unspecified functions, or undefined behavior.
- **Type consistency:** `TermFootnote`, `insert_footnote_markers()`, `_coerce_terms()`, `_extract_financial_terms()`, and `annotate_financial_terms()` are introduced before later tasks reference them.

