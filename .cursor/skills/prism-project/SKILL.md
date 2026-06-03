---
name: prism-project
description: >-
  PRISM-INSIGHT repository layout, prism package imports, MCP config paths, and
  CLI entry points. Use when working anywhere in this repo, onboarding to the
  codebase, fixing import paths, or running demo/orchestrator/trigger commands.
---

# PRISM-INSIGHT project

US stock analysis + KIS trading. Python 3.10+, `mcp-agent`, SQLite, `src/prism` package.

## Layout

- `src/prism/` — application (`core`, `ops`, `trading`, `tracking`, …)
- `src/config/mcp_agent.config.yaml` — MCP servers (no secrets)
- `src/var/` — gitignored outputs (reports, PDFs, logs)
- `src/prism/paths.py` — `REPO_ROOT`, `CONFIG_DIR`, `VAR_ROOT`, `MCP_CONFIG_PATH`
- `pip install -e .` — `prism-demo`, `prism-orchestrator`, …

## Imports

Use `prism.*` only — not legacy `cores`, `scripts`, or top-level `trading`.

```python
from prism.paths import REPORTS_DIR, MCP_CONFIG_PATH
from prism.core.analysis import analyze_us_stock
```

`MCPApp(..., settings=str(MCP_CONFIG_PATH))` — config lives under `src/config/`, not repo root.

## Commands

```bash
pip install -e .
python -m prism.ops.dev.demo AAPL
python -m prism.ops.pipelines.stock_analysis_orchestrator --mode morning
pytest tests/test_multi_account_us.py
```

More: [CURSOR.md](../../../CURSOR.md), [docs/agent-reference.md](../../../docs/agent-reference.md).
