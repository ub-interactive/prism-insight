# Market-Aware Package Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `src/prism` into domain-first `us/`, `cn/`, `shared/` subpackages with short symbol names and shared analysis helpers — no runtime behavior change.

**Architecture:** Move files per the approved spec; rename `USDataClient`→`DataClient`, `analyze_us_stock`→`us.analysis.analyze_stock`, etc. Extract three helpers into `core/shared/analysis_helpers.py` (Option 2a). Clean-break import update across `src/`, `tests/`, `tools/`, docs, and `pyproject.toml` entry points. No compatibility shims.

**Tech Stack:** Python 3.10+, setuptools entry points, pytest, existing mcp-agent stack.

**Spec:** [`docs/superpowers/specs/2026-06-06-market-restructure-design.md`](../specs/2026-06-06-market-restructure-design.md)

**Worktree:** Implement in an isolated worktree (see Task 0) so `main` stays clean during the large move.

---

## File Map

| Area | Action | New location |
|------|--------|--------------|
| `core/report_generation.py` etc. | Move | `core/shared/` |
| `core/analysis.py` | Move + rename fn | `core/us/analysis.py` → `analyze_stock` |
| `core/analysis_cn.py` | Move + rename fn | `core/cn/analysis.py` → `analyze_stock` |
| `core/data/client.py` | Move + rename class | `core/us/data/client.py` → `DataClient` |
| `core/data/cn_client.py` | Move + rename class | `core/cn/data/client.py` → `DataClient` |
| `core/agents/__init__.py` | Move | `core/us/agents/directory.py` |
| `core/agents/cn_directory.py` | Move | `core/cn/agents/directory.py` |
| `core/visualization/chart.py` | Move + rename fns | `core/us/visualization/chart.py` |
| `core/visualization/cn_chart.py` | Move + rename fns | `core/cn/visualization/chart.py` |
| `ops/dev/demo.py` | Move | `ops/shared/dev/demo.py` |
| `ops/pipelines/*` | Move | `ops/us/pipelines/*` |
| `trading/stock_trading.py` | Move + rename class | `trading/us/stock_trading.py` → `StockTrading` |
| `tracking/*.py` | Move | `tracking/us/*.py` |
| `reporting/*.py` | Move | `reporting/shared/*.py` |
| `messaging/*.py` | Move | `messaging/shared/*.py` |
| `integrations/firecrawl_client.py` | Move | `integrations/shared/firecrawl_client.py` |
| `core/shared/analysis_helpers.py` | **Create** | hybrid sections, strategy/summary, finalize |
| `ops/cn/README.md` etc. | **Create** | CN stub placeholders |
| `tests/test_cn_*.py` | Move | `tests/core/cn/test_*.py` |

---

### Task 0: Create isolated worktree

**Files:**
- Create: `.worktrees/market-restructure/` (git worktree)

- [ ] **Step 1: Create worktree branch**

Run from repo root:

```bash
git worktree add .worktrees/market-restructure -b feature/market-restructure
cd .worktrees/market-restructure
pip install -e .
```

Expected: worktree on branch `feature/market-restructure`, editable install succeeds.

- [ ] **Step 2: Baseline test run**

Run:

```bash
pytest tests/test_cn_ticker.py tests/test_cn_client.py tests/test_financial_footnotes.py \
  tests/test_multi_account_us.py tests/test_trading_journal.py -v
```

Expected: all selected tests PASS (record any pre-existing failures).

---

### Task 1: Package skeleton and core package exports

**Files:**
- Create: `src/prism/core/us/__init__.py`
- Create: `src/prism/core/cn/__init__.py`
- Create: `src/prism/core/shared/__init__.py`
- Create: `src/prism/core/__init__.py`
- Create: `src/prism/ops/us/__init__.py`, `ops/cn/__init__.py`, `ops/shared/__init__.py`
- Create: `src/prism/trading/us/__init__.py`, `trading/cn/__init__.py`, `trading/shared/__init__.py`
- Create: `src/prism/tracking/us/__init__.py`, `tracking/cn/__init__.py`, `tracking/shared/__init__.py`
- Create: `src/prism/reporting/us/__init__.py`, `reporting/cn/__init__.py`, `reporting/shared/__init__.py`
- Create: `src/prism/messaging/us/__init__.py`, `messaging/cn/__init__.py`, `messaging/shared/__init__.py`
- Create: `src/prism/integrations/shared/__init__.py`

- [ ] **Step 1: Add core package init**

```python
# src/prism/core/__init__.py
"""Core analysis, data, and agent modules."""

from prism.core import cn, us

__all__ = ["us", "cn"]
```

```python
# src/prism/core/us/__init__.py
"""US market analysis pipeline."""
```

```python
# src/prism/core/cn/__init__.py
"""CN A-share analysis pipeline."""
```

```python
# src/prism/core/shared/__init__.py
"""Cross-market report generation utilities."""
```

- [ ] **Step 2: Add empty __init__.py to all other skeleton dirs**

Each file is a one-line docstring matching its path, e.g.:

```python
# src/prism/ops/us/__init__.py
"""US operational pipelines, batches, and maintenance."""
```

- [ ] **Step 3: Commit**

```bash
git add src/prism/core/__init__.py src/prism/core/us/ src/prism/core/cn/ src/prism/core/shared/ \
  src/prism/ops/ src/prism/trading/ src/prism/tracking/ src/prism/reporting/ \
  src/prism/messaging/ src/prism/integrations/
git commit -m "refactor: add us/cn/shared package skeleton"
```

---

### Task 2: Move core/shared modules

**Files:**
- Move: `core/report_generation.py` → `core/shared/report_generation.py`
- Move: `core/translation.py` → `core/shared/translation.py`
- Move: `core/footnotes.py` → `core/shared/footnotes.py`
- Move: `core/utils.py` → `core/shared/utils.py`
- Move: `core/disclaimer_utils.py` → `core/shared/disclaimer_utils.py`
- Move: `core/config/` → `core/shared/config/`
- Move: `core/llm/` → `core/shared/llm/`
- Move: `core/openai/` → `core/shared/openai/`

- [ ] **Step 1: Git-move shared modules**

```bash
git mv src/prism/core/report_generation.py src/prism/core/shared/report_generation.py
git mv src/prism/core/translation.py src/prism/core/shared/translation.py
git mv src/prism/core/footnotes.py src/prism/core/shared/footnotes.py
git mv src/prism/core/utils.py src/prism/core/shared/utils.py
git mv src/prism/core/disclaimer_utils.py src/prism/core/shared/disclaimer_utils.py
git mv src/prism/core/config src/prism/core/shared/config
git mv src/prism/core/llm src/prism/core/shared/llm
git mv src/prism/core/openai src/prism/core/shared/openai
```

- [ ] **Step 2: Fix internal imports inside moved files**

Replace in all files under `src/prism/core/shared/`:

| Old import | New import |
|------------|------------|
| `from prism.core.config.models` | `from prism.core.shared.config.models` |
| `from prism.core.translation` | `from prism.core.shared.translation` |
| `from prism.core.utils` | `from prism.core.shared.utils` |
| `from prism.core.footnotes` | `from prism.core.shared.footnotes` |
| `from prism.core.report_generation` | `from prism.core.shared.report_generation` |
| `from prism.core.openai` | `from prism.core.shared.openai` |
| `from prism.core.llm` | `from prism.core.shared.llm` |

Example fix in `src/prism/core/shared/footnotes.py`:

```python
from prism.core.shared.config.models import get_configured_model, get_optional_reasoning_effort
from prism.core.shared.translation import extract_and_replace_charts, restore_charts
from prism.core.shared.utils import parse_llm_json
```

- [ ] **Step 3: Verify shared modules compile**

Run:

```bash
python -m py_compile src/prism/core/shared/report_generation.py \
  src/prism/core/shared/footnotes.py src/prism/core/shared/translation.py
```

Expected: no output (success).

- [ ] **Step 4: Commit**

```bash
git add -A src/prism/core/shared/
git commit -m "refactor: move cross-market modules to core/shared"
```

---

### Task 3: Move core/us modules and rename symbols

**Files:**
- Move: `core/analysis.py` → `core/us/analysis.py`
- Move: `core/market_calendar.py` → `core/us/market_calendar.py`
- Move: `core/data/client.py`, `prefetch.py`, `surge_detector.py`, `social_sentiment.py` → `core/us/data/`
- Move: `core/agents/*.py` (except `cn/` and `cn_directory.py`) → `core/us/agents/`
- Move: `core/visualization/chart.py` → `core/us/visualization/chart.py`
- Modify: renamed symbols in moved files

- [ ] **Step 1: Git-move US files**

```bash
mkdir -p src/prism/core/us/data src/prism/core/us/agents src/prism/core/us/visualization
git mv src/prism/core/analysis.py src/prism/core/us/analysis.py
git mv src/prism/core/market_calendar.py src/prism/core/us/market_calendar.py
git mv src/prism/core/data/client.py src/prism/core/us/data/client.py
git mv src/prism/core/data/prefetch.py src/prism/core/us/data/prefetch.py
git mv src/prism/core/data/surge_detector.py src/prism/core/us/data/surge_detector.py
git mv src/prism/core/data/social_sentiment.py src/prism/core/us/data/social_sentiment.py
git mv src/prism/core/visualization/chart.py src/prism/core/us/visualization/chart.py
git mv src/prism/core/agents/company_info_agents.py src/prism/core/us/agents/
git mv src/prism/core/agents/stock_price_agents.py src/prism/core/us/agents/
git mv src/prism/core/agents/news_strategy_agents.py src/prism/core/us/agents/
git mv src/prism/core/agents/market_index_agents.py src/prism/core/us/agents/
git mv src/prism/core/agents/macro_intelligence_agent.py src/prism/core/us/agents/
git mv src/prism/core/agents/trading_agents.py src/prism/core/us/agents/
git mv src/prism/core/agents/trading_journal_agent.py src/prism/core/us/agents/
git mv src/prism/core/agents/__init__.py src/prism/core/us/agents/directory.py
```

- [ ] **Step 2: Rename US symbols**

In `src/prism/core/us/data/client.py`:

```python
class DataClient:  # was USDataClient
    ...

def get_data_client() -> DataClient:  # was get_us_data_client
    return DataClient()
```

In `src/prism/core/us/data/prefetch.py`:

```python
async def prefetch_analysis_data(ticker: str) -> dict:  # was prefetch_us_analysis_data
    ...
```

In `src/prism/core/us/visualization/chart.py`, rename:

- `get_us_price_chart_html` → `get_price_chart_html`
- `get_us_institutional_chart_html` → `get_institutional_chart_html`
- `get_us_technical_chart_html` → `get_technical_chart_html`

In `src/prism/core/us/analysis.py`:

- Rename `analyze_us_stock` → `analyze_stock`
- Rename `_us_market_analysis_cache` → `_market_analysis_cache`
- Rename `clear_us_market_cache` → `clear_market_cache`
- Update imports to `prism.core.shared.*` and `prism.core.us.*`

In `src/prism/core/us/agents/directory.py`, update agent imports:

```python
from prism.core.us.agents.company_info_agents import (
    create_company_overview_agent,
    create_company_status_agent,
)
# ... etc
```

- [ ] **Step 3: Add core/us/data/__init__.py**

```python
from prism.core.us.data.client import DataClient, get_data_client

__all__ = ["DataClient", "get_data_client"]
```

- [ ] **Step 4: Commit**

```bash
git add src/prism/core/us/
git commit -m "refactor: move US core modules to core/us with short names"
```

---

### Task 4: Move core/cn modules and rename symbols

**Files:**
- Move: `core/analysis_cn.py` → `core/cn/analysis.py`
- Move: `core/market_calendar_cn.py` → `core/cn/market_calendar.py`
- Move: `core/market/cn_ticker.py` → `core/cn/market/ticker.py`
- Move: `core/data/cn_client.py`, `cn_prefetch.py` → `core/cn/data/`
- Move: `core/agents/cn/` → `core/cn/agents/`
- Move: `core/agents/cn_directory.py` → `core/cn/agents/directory.py`
- Move: `core/visualization/cn_chart.py` → `core/cn/visualization/chart.py`

- [ ] **Step 1: Git-move CN files**

```bash
mkdir -p src/prism/core/cn/data src/prism/core/cn/market src/prism/core/cn/agents src/prism/core/cn/visualization
git mv src/prism/core/analysis_cn.py src/prism/core/cn/analysis.py
git mv src/prism/core/market_calendar_cn.py src/prism/core/cn/market_calendar.py
git mv src/prism/core/market/cn_ticker.py src/prism/core/cn/market/ticker.py
git mv src/prism/core/data/cn_client.py src/prism/core/cn/data/client.py
git mv src/prism/core/data/cn_prefetch.py src/prism/core/cn/data/prefetch.py
git mv src/prism/core/agents/cn_directory.py src/prism/core/cn/agents/directory.py
git mv src/prism/core/agents/cn/stock_price_agents.py src/prism/core/cn/agents/
git mv src/prism/core/agents/cn/company_info_agents.py src/prism/core/cn/agents/
git mv src/prism/core/agents/cn/market_index_agents.py src/prism/core/cn/agents/
git mv src/prism/core/agents/cn/news_agents.py src/prism/core/cn/agents/
git mv src/prism/core/agents/cn/__init__.py src/prism/core/cn/agents/__init__.py
git mv src/prism/core/visualization/cn_chart.py src/prism/core/cn/visualization/chart.py
```

- [ ] **Step 2: Rename CN symbols**

In `src/prism/core/cn/data/client.py`:

```python
class DataClient:  # was CNDataClient
```

In `src/prism/core/cn/data/prefetch.py`:

```python
def prefetch_analysis_data(code: str, reference_date: str) -> dict:  # was prefetch_cn_analysis_data
```

In `src/prism/core/cn/market/ticker.py` — keep `CNTicker`, `normalize`, `CNTickerError` (ticker types, not market prefix).

In `src/prism/core/cn/market_calendar.py`:

```python
def get_reference_date() -> str:  # was get_cn_reference_date
def is_market_day(d: date) -> bool:  # was is_cn_market_day
```

In `src/prism/core/cn/agents/directory.py`:

```python
def get_agent_directory(...):  # was get_cn_agent_directory
```

In `src/prism/core/cn/visualization/chart.py`:

- `get_cn_price_chart_html` → `get_price_chart_html`
- `get_cn_holder_chart_html` → `get_holder_chart_html`
- `get_cn_technical_chart_html` → `get_technical_chart_html`

In `src/prism/core/cn/analysis.py`:

- `analyze_cn_stock` → `analyze_stock`
- `_cn_market_analysis_cache` → `_market_analysis_cache`
- Update all imports to `prism.core.cn.*` and `prism.core.shared.*`

- [ ] **Step 3: Commit**

```bash
git add src/prism/core/cn/
git commit -m "refactor: move CN core modules to core/cn with short names"
```

---

### Task 5: Shared analysis helpers (TDD)

**Files:**
- Create: `src/prism/core/shared/analysis_helpers.py`
- Test: `tests/core/shared/test_analysis_helpers.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/core/shared/test_analysis_helpers.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from prism.core.shared.analysis_helpers import (
    SEQUENTIAL_DATA_SECTIONS,
    add_strategy_and_summary,
    clean_summary_text,
    finalize_markdown,
)


def test_sequential_sections_constant():
    assert "price_volume_analysis" in SEQUENTIAL_DATA_SECTIONS
    assert len(SEQUENTIAL_DATA_SECTIONS) == 5


def test_clean_summary_text_strips_duplicate_title():
    raw = "# Apple Inc. (AAPL) Analysis Report\n\n**Publication Date:** 2026.06.06\n\nBody"
    cleaned = clean_summary_text(raw, company_name="Apple Inc.", display_symbol="AAPL")
    assert "Apple Inc." not in cleaned.split("Body")[0]
    assert "Body" in cleaned


@pytest.mark.asyncio
async def test_finalize_markdown_english_skips_translation(monkeypatch):
    monkeypatch.setattr(
        "prism.core.shared.analysis_helpers.annotate_financial_terms",
        AsyncMock(return_value="annotated"),
    )
    logger = MagicMock()
    result = await finalize_markdown(logger, "# Report\n", language="en", market="us")
    assert result == "annotated"


@pytest.mark.asyncio
async def test_add_strategy_and_summary_adds_keys(monkeypatch):
    async def fake_strategy(*args, **kwargs):
        return "strategy text"

    async def fake_summary(*args, **kwargs):
        return "summary text"

    monkeypatch.setattr(
        "prism.core.shared.analysis_helpers.generate_investment_strategy",
        fake_strategy,
    )
    monkeypatch.setattr(
        "prism.core.shared.analysis_helpers.generate_summary",
        fake_summary,
    )
    logger = MagicMock()
    sections = {"price_volume_analysis": "pv"}
    out = await add_strategy_and_summary(
        logger,
        sections,
        company_name="Apple Inc.",
        display_symbol="AAPL",
        reference_date="20260606",
        language="en",
    )
    assert "investment_strategy" in out
    assert "summary" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/shared/test_analysis_helpers.py -v`

Expected: FAIL with `ModuleNotFoundError: analysis_helpers`

- [ ] **Step 3: Implement analysis_helpers.py**

```python
# src/prism/core/shared/analysis_helpers.py
"""Shared orchestration helpers for US and CN stock analysis pipelines."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from mcp_agent.app import MCPApp

from prism.core.shared.footnotes import annotate_financial_terms
from prism.core.shared.report_generation import (
    generate_investment_strategy,
    generate_market_report,
    generate_report,
    generate_summary,
)
from prism.core.shared.utils import clean_markdown
from prism.paths import MCP_CONFIG_PATH

SEQUENTIAL_DATA_SECTIONS = [
    "price_volume_analysis",
    "institutional_holdings_analysis",
    "company_status",
    "company_overview",
    "market_index_analysis",
]


def clean_summary_text(summary: str, *, company_name: str, display_symbol: str) -> str:
    """Remove duplicate title/date lines the summary agent may emit."""
    summary = summary.lstrip("\n")
    summary = re.sub(
        r"^#\s*" + re.escape(company_name) + r"\s*\(" + re.escape(display_symbol) + r"\)[^\n]*\n+",
        "",
        summary,
        flags=re.IGNORECASE,
    )
    summary = re.sub(
        r"^\*{0,2}Publication Date\*{0,2}\s*:\s*[^\n]+\n+",
        "",
        summary,
        flags=re.IGNORECASE,
    )
    summary = re.sub(r"^-{3,}\s*\n+", "", summary)
    return summary.lstrip("\n")


async def collect_hybrid_sections(
    logger: Any,
    *,
    agents: dict,
    sequential: list[str],
    parallel: list[str],
    company_name: str,
    display_symbol: str,
    reference_date: str,
    language: str,
    market_cache: dict,
    app_prefix: str,
    base_sections: list[str],
) -> dict[str, str]:
    """Run sequential data sections and parallel news sections; return section_reports."""
    section_reports: dict[str, str] = {}

    async def process_sequential_sections() -> dict[str, str]:
        results: dict[str, str] = {}
        for section in sequential:
            if section not in agents:
                continue
            logger.info(f"Processing {section} for {company_name}...")
            try:
                agent = agents[section]
                if section == "market_index_analysis":
                    if "report" in market_cache:
                        logger.info("Using cached market analysis")
                        report = market_cache["report"]
                    else:
                        logger.info("Generating new market analysis")
                        report = await generate_market_report(
                            agent, section, reference_date, logger, language
                        )
                        market_cache["report"] = report
                else:
                    report = await generate_report(
                        agent,
                        section,
                        company_name,
                        display_symbol,
                        reference_date,
                        logger,
                        language,
                    )
                results[section] = report
                await asyncio.sleep(3)
            except Exception as exc:
                logger.error(f"Error processing {section}: {exc}")
                results[section] = f"Analysis failed: {section}"
        return results

    async def process_parallel_section(section: str):
        if section not in agents:
            return section, None
        section_app = MCPApp(name=f"{app_prefix}_{section}", settings=str(MCP_CONFIG_PATH))
        async with section_app.run() as section_context:
            section_logger = section_context.logger
            section_logger.info(f"Processing {section} for {company_name}...")
            try:
                agent = agents[section]
                report = await generate_report(
                    agent,
                    section,
                    company_name,
                    display_symbol,
                    reference_date,
                    section_logger,
                    language,
                )
                return section, report
            except Exception as exc:
                section_logger.error(f"Error processing {section}: {exc}")
                return section, f"Analysis failed: {section}"

    parallel_tasks = [process_parallel_section(s) for s in parallel]
    sequential_task = process_sequential_sections()
    all_results = await asyncio.gather(sequential_task, *parallel_tasks)

    section_reports.update(all_results[0])
    for result in all_results[1:]:
        if result and result[1] is not None:
            section_reports[result[0]] = result[1]

    return section_reports


async def add_strategy_and_summary(
    logger: Any,
    section_reports: dict[str, str],
    *,
    company_name: str,
    display_symbol: str,
    reference_date: str,
    language: str,
    base_sections: list[str] | None = None,
) -> dict[str, str]:
    """Add investment_strategy and summary to section_reports."""
    sections = list(base_sections or SEQUENTIAL_DATA_SECTIONS)
    if "news_analysis" not in sections:
        sections = sections + ["news_analysis"]

    combined_reports = ""
    for section in sections:
        if section in section_reports:
            combined_reports += f"\n\n--- {section.upper()} ---\n\n"
            combined_reports += section_reports[section]

    try:
        logger.info(f"Processing investment_strategy for {company_name}...")
        investment_strategy = await generate_investment_strategy(
            section_reports,
            combined_reports,
            company_name,
            display_symbol,
            reference_date,
            logger,
            language,
        )
        section_reports["investment_strategy"] = investment_strategy.lstrip("\n")
    except Exception as exc:
        logger.error(f"Error processing investment_strategy: {exc}")
        section_reports["investment_strategy"] = "Investment strategy analysis failed"

    try:
        logger.info(f"Processing summary for {company_name}...")
        summary = await generate_summary(
            section_reports,
            company_name,
            display_symbol,
            reference_date,
            logger,
            language,
        )
        section_reports["summary"] = clean_summary_text(
            summary,
            company_name=company_name,
            display_symbol=display_symbol,
        )
    except Exception as exc:
        logger.error(f"Error processing summary: {exc}")
        section_reports["summary"] = "Summary generation failed"

    return section_reports


async def finalize_markdown(
    logger: Any,
    markdown: str,
    *,
    language: str,
    market: str,
) -> str:
    """Clean markdown, annotate footnotes, optionally translate."""
    del market  # reserved for market-specific finalize hooks later
    markdown = clean_markdown(markdown)
    markdown = await annotate_financial_terms(markdown, language, logger)
    if language and language.lower() != "en":
        from prism.core.shared.translation import translate_report

        markdown = await translate_report(markdown, language)
    return markdown
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/core/shared/test_analysis_helpers.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/prism/core/shared/analysis_helpers.py tests/core/shared/test_analysis_helpers.py
git commit -m "refactor: add shared analysis orchestration helpers"
```

---

### Task 6: Slim US and CN analysis entry points

**Files:**
- Modify: `src/prism/core/us/analysis.py`
- Modify: `src/prism/core/cn/analysis.py`

- [ ] **Step 1: Refactor US analysis to use helpers**

Replace the inline hybrid loop (lines ~141–258) with:

```python
from prism.core.shared import analysis_helpers as shared

# inside analyze_stock(), after agents built:
section_reports = await shared.collect_hybrid_sections(
    logger,
    agents=agents,
    sequential=yfinance_sections,
    parallel=parallel_sections,
    company_name=company_name,
    display_symbol=ticker,
    reference_date=reference_date,
    language=language,
    market_cache=_market_analysis_cache,
    app_prefix="us_stock_analysis",
    base_sections=base_sections,
)
section_reports = await shared.add_strategy_and_summary(
    logger,
    section_reports,
    company_name=company_name,
    display_symbol=ticker,
    reference_date=reference_date,
    language=language,
    base_sections=base_sections,
)
# ... chart + assemble markdown stays in us/analysis.py ...
final_report = await shared.finalize_markdown(
    logger, final_report, language=language, market="us"
)
```

Keep US-only logic in this file: macro_context section, yfinance chart generation, `US_REPORT_FILENAME_MODEL`.

- [ ] **Step 2: Refactor CN analysis similarly**

Same helper calls with `display_code`, `app_prefix="cn_stock_analysis"`, `market="cn"`. Keep CN-only: ticker normalize, `get_reference_date()`, akshare charts.

- [ ] **Step 3: Verify imports compile**

Run:

```bash
python -c "from prism.core import us, cn; print(us.analysis.analyze_stock, cn.analysis.analyze_stock)"
```

Expected: prints two function objects, no ImportError.

- [ ] **Step 4: Commit**

```bash
git add src/prism/core/us/analysis.py src/prism/core/cn/analysis.py
git commit -m "refactor: use shared analysis helpers in US and CN pipelines"
```

---

### Task 7: Move ops modules

**Files:**
- Move: `ops/dev/demo.py` → `ops/shared/dev/demo.py`
- Move: `ops/pipelines/*` → `ops/us/pipelines/`
- Move: `ops/batches/*` → `ops/us/batches/`
- Move: `ops/maintenance/*` → `ops/us/maintenance/`
- Move: `ops/reports/*` → `ops/us/reports/`
- Create: `ops/cn/README.md`

- [ ] **Step 1: Git-move ops files**

```bash
mkdir -p src/prism/ops/shared/dev src/prism/ops/us/pipelines src/prism/ops/us/batches \
  src/prism/ops/us/maintenance src/prism/ops/us/reports
git mv src/prism/ops/dev/demo.py src/prism/ops/shared/dev/demo.py
git mv src/prism/ops/pipelines/stock_analysis_orchestrator.py src/prism/ops/us/pipelines/
git mv src/prism/ops/pipelines/stock_tracking_agent.py src/prism/ops/us/pipelines/
git mv src/prism/ops/pipelines/trigger_batch.py src/prism/ops/us/pipelines/
git mv src/prism/ops/batches/pending_order_batch.py src/prism/ops/us/batches/
git mv src/prism/ops/batches/performance_tracker_batch.py src/prism/ops/us/batches/
git mv src/prism/ops/maintenance/*.py src/prism/ops/us/maintenance/
git mv src/prism/ops/reports/*.py src/prism/ops/us/reports/
git mv src/prism/ops/dev/test_debug_redis.py src/prism/ops/shared/dev/
```

- [ ] **Step 2: Update demo.py to module imports**

```python
# src/prism/ops/shared/dev/demo.py
from prism.core import us, cn

async def generate_report(...):
    if market == "cn":
        from prism.core.cn import market as cn_market
        from prism.core.cn import market_calendar

        ticker = cn_market.ticker.normalize(ticker)
        reference_date = reference_date or market_calendar.get_reference_date()
        report_content = await cn.analysis.analyze_stock(
            code=ticker.code,
            company_name=company_name,
            exchange=ticker.exchange,
            reference_date=reference_date,
            language=language,
            include_news=include_news,
        )
    else:
        report_content = await us.analysis.analyze_stock(
            ticker=ticker,
            company_name=company_name,
            language=language,
            include_news=include_news,
        )
```

Update docstring usage lines to `python -m prism.ops.shared.dev.demo`.

- [ ] **Step 3: Update orchestrator imports**

In `src/prism/ops/us/pipelines/stock_analysis_orchestrator.py`:

```python
from prism.core.us.analysis import analyze_stock
# replace analyze_us_stock(...) with analyze_stock(...)
```

Apply same pattern to `stock_tracking_agent.py`, `trigger_batch.py`, and all moved ops files — replace `prism.core.*` with `prism.core.us.*` or `prism.core.shared.*`.

- [ ] **Step 4: Add ops/cn/README.md**

```markdown
# ops/cn

CN batch orchestration, trigger jobs, and scheduled pipelines are not implemented yet.

Add CN ops entry points here when CN surge detection or batch reporting is built.
```

- [ ] **Step 5: Commit**

```bash
git add src/prism/ops/
git commit -m "refactor: move ops modules to ops/us and ops/shared"
```

---

### Task 8: Move trading and update paths

**Files:**
- Move: `trading/stock_trading.py`, `trading/kis_auth.py`, `trading/config/` → `trading/us/`
- Modify: `src/prism/paths.py`
- Create: `trading/cn/README.md`

- [ ] **Step 1: Git-move trading**

```bash
mkdir -p src/prism/trading/us
git mv src/prism/trading/stock_trading.py src/prism/trading/us/
git mv src/prism/trading/kis_auth.py src/prism/trading/us/
git mv src/prism/trading/config src/prism/trading/us/config
```

- [ ] **Step 2: Rename USStockTrading → StockTrading**

In `src/prism/trading/us/stock_trading.py`:

```python
class StockTrading:  # was USStockTrading
```

Update `if __name__ == "__main__"` block and any self-references.

- [ ] **Step 3: Update paths.py**

```python
TRADING_DIR = SRC_ROOT / "prism" / "trading" / "us"
TRADING_CONFIG_DIR = TRADING_DIR / "config"
```

- [ ] **Step 4: Fix imports across codebase**

Replace:

| Old | New |
|-----|-----|
| `from prism.trading.stock_trading import USStockTrading` | `from prism.trading.us.stock_trading import StockTrading` |
| `from prism.trading.kis_auth` | `from prism.trading.us.kis_auth` |

Run grep to find all:

```bash
rg "prism\.trading\.(stock_trading|kis_auth)" src/ tests/ tools/
```

- [ ] **Step 5: Add trading/cn/README.md and commit**

```bash
git add src/prism/trading/ src/prism/paths.py
git commit -m "refactor: move trading to trading/us, update paths"
```

---

### Task 9: Move tracking modules

**Files:**
- Move: `tracking/journal.py`, `trading_ops.py`, `db_schema.py`, `compression.py`, `helpers.py` → `tracking/us/`
- Modify: `tracking/__init__.py` → re-export from `tracking.us` or move content

- [ ] **Step 1: Git-move tracking files**

```bash
git mv src/prism/tracking/journal.py src/prism/tracking/us/
git mv src/prism/tracking/trading_ops.py src/prism/tracking/us/
git mv src/prism/tracking/db_schema.py src/prism/tracking/us/
git mv src/prism/tracking/compression.py src/prism/tracking/us/
git mv src/prism/tracking/helpers.py src/prism/tracking/us/
```

- [ ] **Step 2: Update tracking/__init__.py**

```python
# src/prism/tracking/__init__.py
from prism.tracking.us.journal import TradingJournal
from prism.tracking.us.db_schema import init_db

__all__ = ["TradingJournal", "init_db"]
```

Adjust exports to match what the old `__init__.py` exported.

- [ ] **Step 3: Update imports in ops/us and tests**

Replace `from prism.tracking.journal` → `from prism.tracking.us.journal` (and siblings).

- [ ] **Step 4: Add tracking/cn/README.md and commit**

```bash
git add src/prism/tracking/
git commit -m "refactor: move tracking modules to tracking/us"
```

---

### Task 10: Move reporting, messaging, integrations

**Files:**
- Move: `reporting/*.py` → `reporting/shared/`
- Move: `messaging/*.py` → `messaging/shared/`
- Move: `integrations/firecrawl_client.py` → `integrations/shared/`

- [ ] **Step 1: Git-move files**

```bash
git mv src/prism/reporting/report_generator.py src/prism/reporting/shared/
git mv src/prism/reporting/pdf_converter.py src/prism/reporting/shared/
git mv src/prism/reporting/analysis_manager.py src/prism/reporting/shared/
git mv src/prism/messaging/redis_signal_publisher.py src/prism/messaging/shared/
git mv src/prism/messaging/redis_health_check.py src/prism/messaging/shared/
git mv src/prism/messaging/gcp_pubsub_signal_publisher.py src/prism/messaging/shared/
git mv src/prism/integrations/firecrawl_client.py src/prism/integrations/shared/
```

- [ ] **Step 2: Update reporting imports**

In `src/prism/reporting/shared/report_generator.py`:

```python
from prism.core import us
from prism.core.us.analysis import analyze_stock
# replace analyze_us_stock with analyze_stock
```

Update `save_cn_report` / `save_us_report` callers to use `prism.core.us` / `prism.core.cn` as needed.

- [ ] **Step 3: Add stub READMEs**

Create `messaging/us/README.md` and `messaging/cn/README.md` noting signal publishers live in `messaging/shared/` today and are US-trading-oriented.

- [ ] **Step 4: Commit**

```bash
git add src/prism/reporting/ src/prism/messaging/ src/prism/integrations/
git commit -m "refactor: move reporting, messaging, integrations to shared subpackages"
```

---

### Task 11: Update pyproject.toml entry points

**Files:**
- Modify: `pyproject.toml`
- Modify: `agents.md`

- [ ] **Step 1: Update entry points**

```toml
[project.scripts]
prism-demo = "prism.ops.shared.dev.demo:main"
prism-orchestrator = "prism.ops.us.pipelines.stock_analysis_orchestrator:cli_main"
prism-tracking = "prism.ops.us.pipelines.stock_tracking_agent:cli_main"
prism-pending-orders = "prism.ops.us.batches.pending_order_batch:main"
prism-trigger-batch = "prism.ops.us.pipelines.trigger_batch:run_cli"
prism-performance-tracker = "prism.ops.us.batches.performance_tracker_batch:main"
prism-weekly-insight = "prism.ops.us.reports.weekly_insight_report:main"
prism-compress-memory = "prism.ops.us.maintenance.compress_trading_memory:main"
prism-update-prices = "prism.ops.us.maintenance.update_current_prices:main"
```

- [ ] **Step 2: Reinstall editable package**

Run: `pip install -e .`

Expected: success, no entry-point errors.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "refactor: update CLI entry points for new package layout"
```

---

### Task 12: Restructure and update tests

**Files:**
- Move/rename tests under `tests/core/us/`, `tests/core/cn/`, `tests/core/shared/`
- Modify: all test imports

- [ ] **Step 1: Create test dirs and move CN tests**

```bash
mkdir -p tests/core/cn tests/core/shared tests/core/us
git mv tests/test_cn_ticker.py tests/core/cn/test_ticker.py
git mv tests/test_cn_market_calendar.py tests/core/cn/test_market_calendar.py
git mv tests/test_cn_client.py tests/core/cn/test_client.py
git mv tests/test_cn_prefetch.py tests/core/cn/test_prefetch.py
git mv tests/test_cn_directory.py tests/core/cn/test_directory.py
git mv tests/test_cn_chart.py tests/core/cn/test_chart.py
git mv tests/test_cn_report_save.py tests/core/cn/test_report_save.py
git mv tests/test_cn_report_generation.py tests/core/cn/test_report_generation.py
git mv tests/test_financial_footnotes.py tests/core/shared/test_financial_footnotes.py
git mv tests/test_translation.py tests/core/shared/test_translation.py
git mv tests/test_model_config.py tests/core/shared/test_model_config.py
git mv tests/test_openai_error_logging.py tests/core/shared/test_openai_error_logging.py
git mv tests/test_strip_trailing_disclaimer.py tests/core/shared/test_strip_trailing_disclaimer.py
```

- [ ] **Step 2: Update CN test imports (example)**

In `tests/core/cn/test_ticker.py`:

```python
from prism.core.cn.market.ticker import CNTicker, normalize, CNTickerError
```

In `tests/core/cn/test_client.py`:

```python
from prism.core.cn.data.client import DataClient

@patch("prism.core.cn.data.client.ak")
```

In `tests/core/cn/test_directory.py`:

```python
from prism.core.cn.agents.directory import get_agent_directory
```

- [ ] **Step 3: Update US-related test imports**

In `tests/test_multi_account_us.py`, `tests/test_trading_journal.py`, etc.:

```python
from prism.trading.us.stock_trading import StockTrading
from prism.trading.us.kis_auth import ...
```

- [ ] **Step 4: Run core test suite**

Run:

```bash
pytest tests/core/ tests/test_multi_account_us.py tests/test_trading_journal.py \
  tests/test_multi_account_kis_auth.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "test: restructure tests to mirror us/cn/shared layout"
```

---

### Task 13: Update documentation

**Files:**
- Modify: `agents.md`
- Modify: `docs/setup.md`
- Modify: `docs/agent-reference.md`
- Modify: `docs/troubleshooting.md`
- Modify: `docs/tasks-reference.md`

- [ ] **Step 1: Update agents.md import examples**

Replace:

```python
from prism.core.analysis import analyze_us_stock
```

With:

```python
from prism.core import us
await us.analysis.analyze_stock(...)
```

Update module table paths, e.g. `src/prism/core/us/agents/stock_price_agents.py`.

- [ ] **Step 2: Update setup.md commands**

```bash
python -m prism.ops.shared.dev.demo AAPL
python -m prism.ops.shared.dev.demo 600519 --market cn --language zh
prism-demo AAPL
```

- [ ] **Step 3: Update agent-reference.md and tasks-reference.md**

Replace all `prism.core.agents.*` paths with `prism.core.us.agents.*` and CN equivalents.

- [ ] **Step 4: Commit**

```bash
git add agents.md docs/
git commit -m "docs: update paths for market-aware package layout"
```

---

### Task 14: Delete stale paths and grep audit

**Files:**
- Delete: empty old dirs (`core/data/`, `core/agents/`, `core/agents/cn/`, `core/market/`, `ops/dev/`, `ops/pipelines/`, etc.)

- [ ] **Step 1: Remove empty legacy directories**

```bash
rm -rf src/prism/core/data src/prism/core/agents src/prism/core/market \
  src/prism/core/visualization src/prism/ops/dev src/prism/ops/pipelines \
  src/prism/ops/batches src/prism/ops/maintenance src/prism/ops/reports
```

Only remove directories confirmed empty or fully migrated.

- [ ] **Step 2: Grep for stale import paths**

Run:

```bash
rg "prism\.core\.(analysis_cn|analysis[^/]|data\.client|data\.cn_|cn_client|cn_prefetch|market_calendar_cn|market\.cn_ticker|agents\.cn_|cn_directory|visualization\.cn_chart|report_generation|translation|footnotes)" \
  src/ tests/ tools/ agents.md docs/ --glob '!docs/superpowers/**'
```

Expected: **zero matches** (excluding historical plan/spec docs under `docs/superpowers/`).

Also grep:

```bash
rg "analyze_us_stock|analyze_cn_stock|USDataClient|CNDataClient|USStockTrading|get_cn_agent_directory|get_us_price_chart|prefetch_us_analysis|prefetch_cn_analysis" \
  src/ tests/ tools/ agents.md docs/ --glob '!docs/superpowers/**'
```

Expected: zero matches.

- [ ] **Step 3: Fix any remaining hits and commit**

```bash
git add -A
git commit -m "refactor: remove legacy flat package paths"
```

---

### Task 15: Full verification

**Files:** (none — verification only)

- [ ] **Step 1: Compile check**

```bash
python -m compileall src/prism -q
```

Expected: no errors.

- [ ] **Step 2: Full pytest (excluding optional integration tests)**

```bash
pytest tests/ -v \
  --ignore=tests/test_integration_pipeline.py \
  --ignore=tests/test_gcp_pubsub_signal.py \
  --ignore=tests/test_redis_signal_pubsub.py
```

Expected: PASS

- [ ] **Step 3: Smoke US demo (dry — no LLM if unavailable)**

Run import check:

```bash
python -c "from prism.ops.shared.dev.demo import main; print('demo ok')"
```

- [ ] **Step 4: Verify entry points**

```bash
pip install -e .
prism-demo --help
prism-orchestrator --help
```

Expected: help text prints, no ImportError.

- [ ] **Step 5: Final commit if any fixups**

```bash
git status
# commit any remaining fixups
git commit -m "chore: verification fixups for market restructure"  # if needed
```

---

## Spec Coverage Checklist

| Spec requirement | Task |
|------------------|------|
| Domain-first us/cn/shared layout | Tasks 1, 7–10 |
| Short symbol names | Tasks 3, 4, 8 |
| Module import style (`from prism.core import us, cn`) | Tasks 6, 7 |
| Shared analysis helpers (Option 2a) | Task 5, 6 |
| Clean break, no shims | Task 14 grep audit |
| CN stubs in US-only domains | Tasks 7, 8, 9, 10 |
| Test layout mirror | Task 12 |
| Docs update | Task 13 |
| pyproject entry points | Task 11 |
| Verification commands | Task 15 |

## Self-Review Notes

- All tasks include exact paths and commands.
- `analysis_helpers.py` and test code are fully specified.
- `get_reference_date` / `is_market_day` CN renames included in Task 4.
- `TRADING_DIR` path update included in Task 8.
- No TBD/TODO placeholders.
