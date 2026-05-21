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

- `cores/`: main analysis engine and AI-powered modules
  - `cores/agents/`: specialized analysis, communication, and trading agents
  - `cores/chatgpt_proxy/`: ChatGPT OAuth proxy for Plus/Pro subscriptions
  - `cores/config/`: model selection (`models.py`) and language settings (`language.py`)
  - `cores/data/`: data access layer — yfinance client, prefetch, surge detection, social sentiment
  - `cores/llm/`: LLM augmentation (OpenAI Responses API)
  - `cores/openai/`: OpenAI integration utilities — debug logging, error helpers, quota checks
  - `cores/visualization/`: chart generation for reports
  - `cores/analysis.py`: sequential orchestration and section integration
  - `cores/report_generation.py`: shared report tone and section formatting rules
- `scripts/`: operational CLIs and batch jobs
- `integrations/`: firebase, Firecrawl, archive API/query
- `reporting/`: PDF/report assembly (`report_generator`, etc.)
- `trading/`: US trading integration and account handling
- `tracking/`: journal, memory, trading state helpers
- `messaging/`: Redis and GCP Pub/Sub messaging
- `tests/`: targeted regression tests (`pytest.ini`: `pythonpath = .`)
- `docs/`: setup, troubleshooting, and agent references
- `examples/`: dashboards, subscriber examples
- `assets/`: static assets (logo, stock_map)
- `repo_paths.py`: canonical `REPO_ROOT`
- Root `*.py` shims: delegate to `scripts/` (same `python demo.py` paths as before)

## Preferred Commands

Use targeted, low-side-effect commands first.

### Setup

```bash
pip install -r requirements.txt
python3 -m playwright install chromium
```

### Local analysis runs

```bash
python stock_analysis_orchestrator.py --mode morning
python demo.py AAPL
python weekly_insight_report.py --dry-run
```

### Focused tests

```bash
pytest tests/test_trading_journal.py
pytest tests/test_multi_account_us.py
```

Avoid broad production-like runs unless the task requires them.

## Change Rules

- Default to safe paths: prefer `--dry-run`, demo mode, or isolated tests.
- Do not commit real credentials, tokens, or secrets in `.env` or `trading/config/kis_devlp.yaml`.
- Treat generated logs, PDFs, JSON outputs, and SQLite databases as user data unless the task explicitly targets them.
- Keep changes narrow and consistent with existing patterns; this repo has substantial behavior encoded in prompts and orchestration order.

## Engineering Rules

### Async and I/O

- In async flows, use non-blocking patterns.
- Do not introduce blocking network calls such as `requests.get(...)` inside async execution paths; use the repo's async approach instead.

### Agent execution

- Preserve sequential execution of analysis agents unless there is clear existing infrastructure for safe parallelism.
- Do not replace sequential report generation with `asyncio.gather(...)` for LLM-heavy sections; rate limits and prompt ordering matter here.
- Market analysis may use cache-aware behavior; preserve that pattern when editing orchestration.

### Trading and data safety

- Default trading behavior should remain safe (`demo` unless explicitly required otherwise).
- Preserve portfolio constraints and stop-loss logic unless the task explicitly changes trading rules.
- When parsing KIS API numeric fields, prefer existing safe conversion helpers over direct casts.

### Report output

- Korean report text must use formal polite style.
- Preserve existing prompt and report structure unless the task explicitly requests prompt/report redesign.

## File-Specific Notes

- `cores/report_generation.py`: common report tone and section formatting rules
- `cores/analysis.py`: sequential orchestration and section integration
- `cores/agents/*.py`: prompt logic and agent responsibilities
- `cores/config/models.py`: model IDs from `mcp_agent.config.yaml`
- `cores/data/prefetch.py`: yfinance data pre-fetch (eliminates MCP round-trips)
- `cores/data/surge_detector.py`: US surge/momentum detection algorithms
- `stock_tracking_agent.py`: trading loop, sell decisions, optional journal flow

## Before Finishing

- Run the smallest relevant test or command that validates the change.
- If you could not run validation, say so explicitly and explain why.
- In summaries, reference the files changed and note any operational risk, especially around trading, messaging, or credential handling.

## Cursor Cloud specific instructions

### Environment

- Python 3.12, Node.js 22.x are available.
- `PATH` must include `/home/ubuntu/.local/bin` (where pip installs CLI tools like `playwright`, `ruff`, `pytest`).
- Config files: copy `*.example` files if the non-example counterparts are missing (`mcp_agent.config.yaml` is tracked; `.env` and `trading/config/kis_devlp.yaml` are not).

### Running services

- The application is a **batch/cron-driven pipeline**, not a long-running server. There is no `dev server` to start.
- `python weekly_insight_report.py --dry-run` is the fastest smoke test (no API keys needed).
- `python demo.py AAPL` runs the full analysis pipeline; it requires `OPENAI_API_KEY` in `mcp_agent.secrets.yaml` (or `.env` after config refactor) to succeed past data prefetch.
- Tests: `pytest tests/` — ignore `test_gcp_pubsub_signal.py`, `test_redis_signal_pubsub.py`, `test_integration_pipeline.py`, and `test_journal_schema_smoke.py` (these need external services or specific DB state).

### Linting

- No formal linter is configured in the repo. Use `ruff check --select E,F` for quick syntax/import checks.

### Backward-compatible shims

- Root-level Python files (e.g., `demo.py`, `stock_analysis_orchestrator.py`) are shims that delegate to `scripts/`.
- Old `cores/*.py` flat imports (e.g., `cores.model_config`) are shims that re-export from `cores/config/`, `cores/data/`, `cores/openai/`, `cores/visualization/`.
