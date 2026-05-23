# AGENTS.md - Codex Guide for PRISM-INSIGHT

This file governs the repository rooted here.

## Project Summary

PRISM-INSIGHT is an AI-powered US stock analysis and automated trading system built around:

- Python 3.10+
- GPT-5 / Claude based analysis agents
- SQLite storage
- KIS trading APIs
- US market flows

Primary source material for project context lives in `CLAUDE.md` and supporting docs under `docs/`.

## Repository Map

```
prism-insight/
├── README.md, LICENSE, pyproject.toml, requirements.txt
├── deploy/              # Dockerfile, docker/, quickstart.sh
├── src/
│   ├── config/          # mcp_agent.config.yaml (no secrets)
│   ├── var/             # gitignored outputs (reports, pdf, logs, triggers)
│   ├── vendor/sqlite/   # MCP sqlite server
│   └── prism/           # Application package
│       ├── core/, ops/, reporting/, integrations/, trading/, tracking/, messaging/
│       └── paths.py     # REPO_ROOT, SRC_ROOT, config/var paths
├── tests/, examples/, assets/, tools/
├── demo.py, stock_analysis_orchestrator.py, …  # thin root CLI shims (5 files)
└── repo_paths.py        # backward-compat → prism.paths
```

## Preferred Commands

```bash
pip install -e .
pip install -r requirements.txt
python3 -m playwright install chromium
```

```bash
python stock_analysis_orchestrator.py --mode morning
python demo.py AAPL
prism-demo AAPL   # after pip install -e .
```

```bash
pytest tests/test_trading_journal.py tests/test_multi_account_us.py
```

## Change Rules

- Default to safe paths: prefer `--dry-run`, demo mode, or isolated tests.
- Do not commit real credentials in `.env` or `**/trading/config/kis_devlp.yaml`.
- Import canonical modules: `prism.core.*`, `prism.ops.*`, `prism.paths` — not legacy `cores` or `scripts`.

## Engineering Rules

- Async I/O in async flows; no blocking `requests` in async paths.
- Sequential LLM agent execution (no `asyncio.gather` on report sections).
- Korean report text: formal polite style (합쇼체).
- KIS numeric fields: use existing safe conversion helpers.

## File-Specific Notes

- `src/prism/core/analysis.py` — sequential orchestration
- `src/prism/core/config/models.py` — reads `src/config/mcp_agent.config.yaml`
- `src/prism/paths.py` — `REPO_ROOT`, `src/var/reports`, `TRADING_CONFIG_DIR`
- `src/prism/ops/pipelines/` — cron entry implementations

## Before Finishing

- Run the smallest relevant pytest subset.
- Root shims and `pip install -e .` console scripts (`prism-demo`, etc.) should both work.
