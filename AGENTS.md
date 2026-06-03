# AGENTS.md — Cursor / Codex guide

Instructions for AI agents working in this repository.

## Start here

1. **Skills** — `.cursor/skills/` (`prism-project`, `prism-python`, `prism-trading`, `prism-reports`)
2. **Full guide** — [`CURSOR.md`](CURSOR.md)
3. **Setup** — [`docs/setup.md`](docs/setup.md)

## Project

PRISM-INSIGHT: US stock analysis + KIS trading. Package: `src/prism`. Install: `pip install -e .`.

```
src/prism/{core,ops,trading,tracking,reporting,integrations,messaging}
src/config/   src/var/   src/vendor/sqlite/
```

Import `prism.*` only (not `cores`, `scripts`, or root `trading`).

## Commands

```bash
pip install -e .
python -m prism.ops.dev.demo AAPL
python -m prism.ops.pipelines.stock_analysis_orchestrator --mode morning
pytest tests/test_multi_account_us.py tests/test_trading_journal.py
```

Skip unless required: `test_gcp_pubsub_signal.py`, `test_redis_signal_pubsub.py`, `test_integration_pipeline.py`.

## Safety

- Prefer `--dry-run` and **demo** trading mode
- No secrets in git (`.env`, `kis_devlp.yaml`, `mcp_agent.secrets.yaml`)
- Sequential LLM agents; async-safe I/O

## Deep dives

| Topic | File |
|-------|------|
| Agents | `docs/agent-reference.md` |
| Troubleshooting | `docs/troubleshooting.md` |
| Tasks | `docs/tasks-reference.md` |
| Paths / reports | `src/prism/paths.py` |
