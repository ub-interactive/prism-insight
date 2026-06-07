# Market-Aware Package Restructure — Design Spec

**Date:** 2026-06-06  
**Status:** Approved  
**Scope:** Full `prism` package layout (analysis, ops, trading, tracking, reporting, messaging)

---

## 1. Goals

### Goal

Restructure the codebase so US-only, CN-only, and shared logic are immediately obvious from the package tree and import paths — without changing runtime behavior.

### Success Criteria

- Every top-level domain (`core`, `ops`, `trading`, `tracking`, `reporting`, `messaging`) uses a consistent `us/`, `cn/`, `shared/` layout.
- Market identity lives in the package path; symbols inside `us/` and `cn/` drop redundant `us_` / `cn_` prefixes.
- Call sites that touch both markets import modules (`from prism.core import us, cn`).
- US demo, orchestrator, and trading tests pass after a clean-break import update.
- CN demo (`--market cn`) still produces markdown + PDF.

### Out of Scope

- CN trading, tracking, batch orchestrator, or surge detection implementation.
- Import-lint / CI enforcement of cross-market boundaries.
- Optional dependency splits (e.g. `akshare` extras).
- Compatibility shims or deprecation period for old import paths.

---

## 2. Decisions (Approved)

| Topic | Choice |
|-------|--------|
| Scope | Full package — all top-level domains |
| Layout | Domain-first: `us/`, `cn/`, `shared/` under each domain |
| Migration | Clean break — update all imports in one pass, no shims |
| US-only domains today | Empty `cn/` stubs (`README.md` + minimal `__init__.py`) for consistent shape |
| Shared pipeline | **Option 2a** — extract duplicated blocks as plain helpers only; no pipeline framework |
| Imports at call sites | Module style: `from prism.core import us, cn` |
| Naming | Short names within market folders (`analyze_stock`, `DataClient`, not `analyze_us_stock`) |

---

## 3. Target Package Tree

```
src/prism/
├── paths.py
│
├── core/
│   ├── us/
│   │   ├── analysis.py              # analyze_stock()
│   │   ├── market_calendar.py
│   │   ├── data/
│   │   │   ├── client.py            # DataClient (was USDataClient)
│   │   │   ├── prefetch.py
│   │   │   ├── surge_detector.py
│   │   │   └── social_sentiment.py
│   │   ├── agents/
│   │   │   ├── directory.py         # get_agent_directory()
│   │   │   ├── company_info_agents.py
│   │   │   ├── stock_price_agents.py
│   │   │   ├── news_strategy_agents.py
│   │   │   ├── market_index_agents.py
│   │   │   └── macro_intelligence_agent.py
│   │   └── visualization/
│   │       └── chart.py
│   ├── cn/
│   │   ├── analysis.py              # analyze_stock()
│   │   ├── market_calendar.py
│   │   ├── market/
│   │   │   └── ticker.py
│   │   ├── data/
│   │   │   ├── client.py            # DataClient (was CNDataClient)
│   │   │   └── prefetch.py
│   │   ├── agents/
│   │   │   ├── directory.py
│   │   │   ├── company_info_agents.py
│   │   │   ├── stock_price_agents.py
│   │   │   ├── news_agents.py
│   │   │   └── market_index_agents.py
│   │   └── visualization/
│   │       └── chart.py
│   └── shared/
│       ├── analysis_helpers.py      # NEW — hybrid sections, strategy/summary, finalize
│       ├── report_generation.py
│       ├── translation.py
│       ├── footnotes.py
│       ├── utils.py
│       ├── disclaimer_utils.py
│       ├── config/
│       ├── llm/
│       └── openai/
│
├── ops/
│   ├── us/
│   │   ├── pipelines/               # orchestrator, tracking_agent, trigger_batch
│   │   ├── batches/
│   │   ├── maintenance/
│   │   └── reports/
│   ├── cn/
│   │   ├── README.md
│   │   └── __init__.py
│   └── shared/
│       └── dev/
│           └── demo.py              # prism-demo entry; routes --market us|cn
│
├── trading/
│   ├── us/
│   │   ├── stock_trading.py         # StockTrading (was USStockTrading)
│   │   ├── kis_auth.py
│   │   └── config/
│   ├── cn/
│   │   ├── README.md
│   │   └── __init__.py
│   └── shared/
│       └── __init__.py
│
├── tracking/
│   ├── us/
│   │   ├── journal.py
│   │   ├── trading_ops.py
│   │   ├── db_schema.py
│   │   ├── compression.py
│   │   └── helpers.py
│   ├── cn/
│   │   ├── README.md
│   │   └── __init__.py
│   └── shared/
│       └── __init__.py
│
├── reporting/
│   ├── us/
│   │   └── __init__.py              # reserved for US-only report hooks
│   ├── cn/
│   │   └── fonts.py                 # CJK font resolution (split from pdf_converter if needed)
│   └── shared/
│       ├── report_generator.py
│       ├── pdf_converter.py
│       └── analysis_manager.py
│
├── messaging/
│   ├── us/
│   │   ├── README.md
│   │   └── __init__.py
│   ├── cn/
│   │   ├── README.md
│   │   └── __init__.py
│   └── shared/
│       ├── redis_signal_publisher.py
│       ├── redis_health_check.py
│       └── gcp_pubsub_signal_publisher.py
│
└── integrations/
    └── shared/
        └── firecrawl_client.py
```

---

## 4. Naming & Import Conventions

### Rule

Market identity is encoded in the package path. Files and symbols inside `us/` and `cn/` use the short name.

### Examples

| Old | New |
|-----|-----|
| `prism.core.analysis.analyze_us_stock` | `prism.core.us.analysis.analyze_stock` |
| `prism.core.analysis_cn.analyze_cn_stock` | `prism.core.cn.analysis.analyze_stock` |
| `prism.core.data.client.USDataClient` | `prism.core.us.data.client.DataClient` |
| `prism.core.data.cn_client.CNDataClient` | `prism.core.cn.data.client.DataClient` |
| `prefetch_us_analysis_data` | `prism.core.us.data.prefetch.prefetch_analysis_data` |
| `prefetch_cn_analysis_data` | `prism.core.cn.data.prefetch.prefetch_analysis_data` |
| `get_cn_agent_directory` | `prism.core.cn.agents.directory.get_agent_directory` |
| `get_us_price_chart_html` | `prism.core.us.visualization.chart.get_price_chart_html` |
| `get_cn_price_chart_html` | `prism.core.cn.visualization.chart.get_price_chart_html` |
| `prism.core.market.cn_ticker.normalize` | `prism.core.cn.market.ticker.normalize` |
| `prism.core.market_calendar_cn` | `prism.core.cn.market_calendar` |
| `prism.trading.stock_trading.USStockTrading` | `prism.trading.us.stock_trading.StockTrading` |
| `prism.ops.pipelines.stock_analysis_orchestrator` | `prism.ops.us.pipelines.stock_analysis_orchestrator` |
| `prism.ops.dev.demo` | `prism.ops.shared.dev.demo` |

### Preferred call-site style

Import market packages as modules:

```python
from prism.core import us, cn

await us.analysis.analyze_stock(ticker="AAPL", company_name="Apple Inc.", ...)
await cn.analysis.analyze_stock(code="600519", company_name="...", exchange="SH", ...)
```

Submodules for data and utilities:

```python
from prism.core.us import data as us_data
client = us_data.client.DataClient()

from prism.core.cn import market as cn_market
ticker = cn_market.ticker.normalize("600519")
```

Do **not** re-export `analyze_stock` at `prism.core.us` package root — callers use `us.analysis.analyze_stock`.

### Entry points (`pyproject.toml`)

| Script | New target |
|--------|------------|
| `prism-demo` | `prism.ops.shared.dev.demo:main` |
| `prism-orchestrator` | `prism.ops.us.pipelines.stock_analysis_orchestrator:cli_main` |
| `prism-tracking` | `prism.ops.us.pipelines.stock_tracking_agent:cli_main` |
| `prism-trigger-batch` | `prism.ops.us.pipelines.trigger_batch:run_cli` |
| `prism-pending-orders` | `prism.ops.us.batches.pending_order_batch:main` |
| `prism-performance-tracker` | `prism.ops.us.batches.performance_tracker_batch:main` |
| `prism-weekly-insight` | `prism.ops.us.reports.weekly_insight_report:main` |
| `prism-compress-memory` | `prism.ops.us.maintenance.compress_trading_memory:main` |
| `prism-update-prices` | `prism.ops.us.maintenance.update_current_prices:main` |

---

## 5. Shared Analysis Helpers (Option 2a)

No pipeline framework, state object, or hook registry. Extract only the duplicated orchestration blocks into `core/shared/analysis_helpers.py`.

### `collect_hybrid_sections`

Owns sequential data-section loop + parallel news sections + market-index cache.

```python
async def collect_hybrid_sections(
    logger,
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
) -> dict[str, str]:
    ...
```

Both markets pass the same `sequential` section names:

```python
SEQUENTIAL_DATA_SECTIONS = [
    "price_volume_analysis",
    "institutional_holdings_analysis",
    "company_status",
    "company_overview",
    "market_index_analysis",
]
```

### `add_strategy_and_summary`

Owns investment-strategy LLM call, executive-summary LLM call, and summary title/date cleanup.

```python
async def add_strategy_and_summary(
    logger,
    section_reports: dict[str, str],
    *,
    company_name: str,
    display_symbol: str,
    reference_date: str,
    language: str,
) -> dict[str, str]:
    ...
```

### `finalize_markdown`

Owns footnote annotation and optional translation.

```python
async def finalize_markdown(
    logger,
    markdown: str,
    *,
    language: str,
    market: str,
) -> str:
    ...
```

### Market entry points remain linear scripts

Each `analyze_stock()` reads top-to-bottom:

1. Resolve reference date (market-specific)
2. Open MCP session
3. Prefetch data (market-specific)
4. Build agents (market-specific)
5. `shared.collect_hybrid_sections(...)`
6. `shared.add_strategy_and_summary(...)`
7. Build charts (market-specific)
8. Assemble markdown (market-specific layout; may stay inline)
9. `shared.finalize_markdown(...)`
10. Save report + PDF (market-specific)

US and CN files differ in steps 1–4, 7, and 10; steps 5–6 and 9 are shared.

---

## 6. File Migration Map (Core)

| Current path | New path |
|--------------|----------|
| `core/analysis.py` | `core/us/analysis.py` |
| `core/analysis_cn.py` | `core/cn/analysis.py` |
| `core/market_calendar.py` | `core/us/market_calendar.py` |
| `core/market_calendar_cn.py` | `core/cn/market_calendar.py` |
| `core/market/cn_ticker.py` | `core/cn/market/ticker.py` |
| `core/data/client.py` | `core/us/data/client.py` |
| `core/data/prefetch.py` | `core/us/data/prefetch.py` |
| `core/data/surge_detector.py` | `core/us/data/surge_detector.py` |
| `core/data/social_sentiment.py` | `core/us/data/social_sentiment.py` |
| `core/data/cn_client.py` | `core/cn/data/client.py` |
| `core/data/cn_prefetch.py` | `core/cn/data/prefetch.py` |
| `core/agents/*.py` (US) | `core/us/agents/*.py` |
| `core/agents/cn/*.py` | `core/cn/agents/*.py` |
| `core/agents/cn_directory.py` | `core/cn/agents/directory.py` |
| `core/agents/__init__.py` (US directory) | `core/us/agents/directory.py` |
| `core/visualization/chart.py` | `core/us/visualization/chart.py` |
| `core/visualization/cn_chart.py` | `core/cn/visualization/chart.py` |
| `core/report_generation.py` | `core/shared/report_generation.py` |
| `core/translation.py` | `core/shared/translation.py` |
| `core/footnotes.py` | `core/shared/footnotes.py` |
| `core/utils.py` | `core/shared/utils.py` |
| `core/disclaimer_utils.py` | `core/shared/disclaimer_utils.py` |
| `core/config/` | `core/shared/config/` |
| `core/llm/` | `core/shared/llm/` |
| `core/openai/` | `core/shared/openai/` |

Old paths are deleted after migration — no re-export shims.

---

## 7. CN Stubs (US-Only Domains Today)

Each stub includes a short `README.md` explaining the domain is US-only for now and where to add CN code later.

| Package | Stub contents |
|---------|---------------|
| `ops/cn/` | README only |
| `trading/cn/` | README + `__init__.py` |
| `tracking/cn/` | README + `__init__.py` |
| `messaging/us/` | README + `__init__.py` (signals tied to US trading today) |
| `messaging/cn/` | README + `__init__.py` |

No `NotImplementedError` at import time — stubs are documentation placeholders, not runtime gates.

---

## 8. Tests

Mirror source layout under `tests/`:

```
tests/
├── core/
│   ├── us/          # was test_multi_account_us-adjacent, surge, etc.
│   ├── cn/          # test_cn_*.py renamed/moved
│   └── shared/      # test_financial_footnotes, test_translation, test_model_config
├── trading/us/
├── tracking/us/
└── conftest.py
```

Short filenames within market folders (`test_client.py`, not `test_cn_client.py`).

---

## 9. Documentation Updates

Update import examples and module paths in:

- `agents.md`
- `docs/setup.md`
- `docs/agent-reference.md`
- `docs/troubleshooting.md`
- `docs/tasks-reference.md`

---

## 10. Migration Plan (Single Clean-Break PR)

1. Create `us/`, `cn/`, `shared/` skeleton under each domain.
2. Move and rename files per migration map.
3. Add `core/shared/analysis_helpers.py`; slim down `us/analysis.py` and `cn/analysis.py`.
4. Update all imports in `src/`, `tests/`, `tools/`.
5. Update `pyproject.toml` entry points.
6. Add CN stub READMEs.
7. Delete old flat paths.
8. Run verification:
   - `pytest tests/ -v` (excluding optional integration tests per AGENTS.md)
   - `python -m prism.ops.shared.dev.demo AAPL --market us` (or `prism-demo AAPL`)
   - `python -m prism.ops.shared.dev.demo 600519 --market cn --language zh`

---

## 11. Architecture Diagram

```mermaid
flowchart TB
    subgraph ops_shared [ops/shared]
        Demo[demo.py --market us|cn]
    end

    subgraph core_us [core/us]
        USAnalysis[analysis.analyze_stock]
        USData[data.client.DataClient]
        USAgents[agents.directory]
    end

    subgraph core_cn [core/cn]
        CNAnalysis[analysis.analyze_stock]
        CNData[data.client.DataClient]
        CNAgents[agents.directory]
    end

    subgraph core_shared [core/shared]
        Helpers[analysis_helpers]
        ReportGen[report_generation]
        Footnotes[footnotes]
        Translation[translation]
    end

    Demo -->|market us| USAnalysis
    Demo -->|market cn| CNAnalysis

    USAnalysis --> Helpers
    CNAnalysis --> Helpers
    USAnalysis --> USData
    USAnalysis --> USAgents
    CNAnalysis --> CNData
    CNAnalysis --> CNAgents

    Helpers --> ReportGen
    Helpers --> Footnotes
    Helpers --> Translation
```

---

## 12. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Large diff touches many files | Move-first commits; run tests after import sweep |
| Missed import after clean break | Grep for old paths (`analysis_cn`, `cn_client`, `USDataClient`) before merge |
| Helper extraction changes behavior | Keep helper bodies copied verbatim from existing analysis files initially |
| Entry-point scripts break | Update `pyproject.toml` and verify `pip install -e .` |
