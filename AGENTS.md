# AGENTS.md — Cursor / PRISM-INSIGHT Project Guide

Instructions and references for AI agents and assistants working in this repository.

## Start here

1. **Skills** — `.cursor/skills/` (`prism-project`, `prism-python`, `prism-trading`, `prism-reports`)
2. **Setup** — [`docs/setup.md`](docs/setup.md)
3. **Troubleshooting** — [`docs/troubleshooting.md`](docs/troubleshooting.md)

---

## Project Overview

**PRISM-INSIGHT** — AI-powered US stock analysis and automated trading.
- **Package**: `src/prism` (install: `pip install -e .`)
- **Root paths**: `src/prism/paths.py` (`REPO_ROOT`, `CONFIG_DIR`, `VAR_ROOT`, `MCP_CONFIG_PATH`)

```
src/prism/{core,ops,trading,tracking,reporting,integrations,messaging}
src/config/   src/var/   src/vendor/sqlite/
```

### Import Rules
Import `prism.*` only. Do **not** import legacy `cores`, `scripts`, or root `trading`.
```python
from prism.paths import REPORTS_DIR, MCP_CONFIG_PATH
from prism.core.analysis import analyze_us_stock
```

---

## Repository Layout

```
prism-insight/
├── AGENTS.md                  # Comprehensive agent instructions (this file)
├── .cursor/skills/            # Project skills (prism-project, prism-python, …)
├── src/
│   ├── config/                # mcp_agent.config.yaml
│   ├── var/                   # reports, pdf_reports, logs (gitignored)
│   ├── vendor/sqlite/         # MCP sqlite server
│   └── prism/                 # Application package
└── docs/                      # setup, agent-reference, troubleshooting, …
```

---

## Analysis & Trading Pipeline

```
prism.ops.pipelines.trigger_batch → candidates JSON
prism.ops.pipelines.stock_analysis_orchestrator → prefetch → 6 analysts (sequential) → strategist → PDF
prism.ops.pipelines.stock_tracking_agent → buy/sell (cron, multi-account)
```

Agent orchestration table and prompts: [`docs/agent-reference.md`](docs/agent-reference.md).

| # | Agent | Module |
|---|-------|--------|
| 1–2 | Technical / Flow | `src/prism/core/agents/stock_price_agents.py` |
| 3–4 | Financial / Industry | `src/prism/core/agents/company_info_agents.py` |
| 5–7 | News / Market / Strategist | `src/prism/core/agents/news_strategy_agents.py`, `market_index_agents.py` |
| 8 | Macro Intelligence | `src/prism/core/agents/macro_intelligence_agent.py` |
| 9–11 | Journal / Buy / Sell | `trading_journal_agent.py`, `trading_agents.py` |

Orchestration logic: `src/prism/core/analysis.py`.

---

## Commands

| Command | Purpose |
|---------|---------|
| `python -m prism.ops.dev.demo AAPL` | Single-stock report |
| `python -m prism.ops.pipelines.stock_analysis_orchestrator --mode morning` | Morning batch |
| `python -m prism.ops.pipelines.trigger_batch morning INFO` | Surge detection only |
| `python -m prism.ops.batches.pending_order_batch --dry-run` | Pending orders dry run |
| `prism-demo AAPL` | Same as demo (after `pip install -e .` entry point) |
| `pytest tests/test_multi_account_us.py tests/test_trading_journal.py` | Run core verification tests |

*Skip unless required*: `test_gcp_pubsub_signal.py`, `test_redis_signal_pubsub.py`, `test_integration_pipeline.py`.

---

## Configuration

| File | Purpose |
|------|---------|
| `.env` | API keys, Redis/GCP toggles |
| `src/config/mcp_agent.config.yaml` | MCP servers configuration (no secrets) |
| `src/prism/trading/config/kis_devlp.yaml` | KIS credentials (gitignored) |

Copy `.env.example` → `.env`. The MCP config path is passed explicitly to `MCPApp` via `MCP_CONFIG_PATH`.

---

## Safety & Engineering Rules

- **Prefer `--dry-run` and demo trading mode** for safety.
- **No secrets in git** (never commit `.env`, `kis_devlp.yaml`, or `mcp_agent.secrets.yaml`).
- **Sequential LLM agent invocation**: Generate report sections sequentially (no `asyncio.gather` on agent endpoints).
- **Asynchronous non-blocking I/O**: Use async in async paths; do not use blocking `requests`.
- **KIS numbers**: Use `_safe_float` / `_safe_int` from `prism.trading.stock_trading`.
- **Reports**: Reports must be generated in English.
- **Trading**: Respect slot and sector limits.

---

## US Trading Notes

- Market hours: 09:30–16:00 EST.
- Reserved orders when closed: buy needs `limit_price`; sell may use MOO.
- Multi-account: Supports all `accounts` configured in `kis_devlp.yaml`.

---

## Deep Dives & Related Docs

| Topic | File |
|-------|------|
| Agents Details | [`docs/agent-reference.md`](docs/agent-reference.md) |
| Troubleshooting | [`docs/troubleshooting.md`](docs/troubleshooting.md) |
| Task Playbooks | [`docs/tasks-reference.md`](docs/tasks-reference.md) |
| Environment Setup | [`docs/setup.md`](docs/setup.md) |
| Paths / Reports | `src/prism/paths.py` |
