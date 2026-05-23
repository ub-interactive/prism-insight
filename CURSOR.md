# CURSOR.md — PRISM-INSIGHT project guide

> **Version**: 2.9.0 | **For**: Cursor IDE, Cloud Agents, and other coding agents

Cursor loads **`AGENTS.md`** and project **skills** under **`.cursor/skills/`** automatically. This file is the full reference.

## Overview

**PRISM-INSIGHT** — AI-powered US stock analysis and automated trading.

```yaml
Stack: Python 3.10+, mcp-agent, GPT-5 / Claude, SQLite, KIS API
Package: src/prism (install: pip install -e .)
```

## Repository layout

```
prism-insight/
├── AGENTS.md, CURSOR.md       # Agent instructions (Cursor reads AGENTS.md)
├── .cursor/skills/            # Project skills (prism-project, prism-python, …)
├── deploy/                    # Docker, crontab, entrypoints
├── src/
│   ├── config/                # mcp_agent.config.yaml
│   ├── var/                   # reports, pdf_reports, logs (gitignored)
│   ├── vendor/sqlite/         # MCP sqlite server
│   └── prism/                 # Application package
├── demo.py, stock_analysis_orchestrator.py, …  # root CLI shims (5 files)
└── docs/                      # SETUP, agent-reference, troubleshooting, …
```

Paths: `src/prism/paths.py` (`REPO_ROOT`, `CONFIG_DIR`, `VAR_ROOT`, `MCP_CONFIG_PATH`).

## Analysis pipeline

```
trigger_batch.py → candidates JSON
stock_analysis_orchestrator.py → prefetch → 6 analysts (sequential) → strategist → PDF
stock_tracking_agent.py → buy/sell (cron, multi-account)
```

Agent table and prompts: [`docs/agent-reference.md`](docs/agent-reference.md).

| # | Agent | Module |
|---|-------|--------|
| 1–2 | Technical / Flow | `src/prism/core/agents/stock_price_agents.py` |
| 3–4 | Financial / Industry | `src/prism/core/agents/company_info_agents.py` |
| 5–7 | News / Market / Strategist | `src/prism/core/agents/news_strategy_agents.py`, `market_index_agents.py` |
| 8 | Macro Intelligence | `src/prism/core/agents/macro_intelligence_agent.py` |
| 9–11 | Journal / Buy / Sell | `trading_journal_agent.py`, `trading_agents.py` |

Orchestration: `src/prism/core/analysis.py`.

## Commands

| Command | Purpose |
|---------|---------|
| `python demo.py AAPL` | Single-stock report |
| `python stock_analysis_orchestrator.py --mode morning` | Morning batch |
| `python trigger_batch.py morning INFO` | Surge detection only |
| `python pending_order_batch.py --dry-run` | Pending orders dry run |
| `prism-demo AAPL` | Same as demo (after `pip install -e .`) |
| `PRISM_OPENAI_AUTH_MODE=chatgpt_oauth python demo.py AAPL` | ChatGPT OAuth proxy |

## Configuration

| File | Purpose |
|------|---------|
| `.env` | API keys, Redis/GCP toggles (`PRISM_OPENAI_AUTH_MODE`, …) |
| `src/config/mcp_agent.config.yaml` | MCP servers (no secrets) |
| `src/prism/trading/config/kis_devlp.yaml` | KIS credentials (gitignored) |

Copy `.env.example` → `.env`. MCP config path is passed explicitly to `MCPApp` via `MCP_CONFIG_PATH`.

ChatGPT OAuth login:

```bash
python -m prism.core.chatgpt_proxy.oauth_login
```

## Engineering rules

See `.cursor/skills/` (see [README](.cursor/skills/README.md)). Summary:

- **Async** in async paths; no blocking `requests`
- **Sequential** LLM report sections (no `asyncio.gather` on agents)
- **KIS numbers**: `_safe_float` / `_safe_int` from `prism.trading.stock_trading`
- **Reports**: English only
- **Trading**: default `demo`; respect slot/sector limits

## US trading notes

- Market hours: 09:30–16:00 EST
- Reserved orders when closed: buy needs `limit_price`; sell may use MOO
- Multi-account: all `accounts` in `kis_devlp.yaml`

## Troubleshooting

| Issue | Fix |
|-------|-----|
| MCP config not found | Use `MCP_CONFIG_PATH`; file is `src/config/mcp_agent.config.yaml` |
| KIS auth | `src/prism/trading/config/kis_devlp.yaml` |
| Playwright PDF | `python3 -m playwright install chromium` |
| ChatGPT OAuth | `python -m prism.core.chatgpt_proxy.oauth_login` |

More: [`docs/troubleshooting.md`](docs/troubleshooting.md).

## Git workflow

- Code changes (`.py`, etc.): feature branch + PR (`feat/`, `fix/`, …)
- Docs-only: may commit on `main`
- Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

## Related docs

| Doc | Content |
|-----|---------|
| [`docs/agent-reference.md`](docs/agent-reference.md) | Agent system detail |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | Extended troubleshooting |
| [`docs/tasks-reference.md`](docs/tasks-reference.md) | Task playbooks |
| [`docs/SETUP.md`](docs/SETUP.md) | Environment setup |
