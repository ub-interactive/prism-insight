---
name: prism-python
description: >-
  Python conventions for PRISM-INSIGHT: async I/O, sequential LLM agent runs,
  KIS safe numeric parsing, and secret handling. Use when editing files under
  src/, especially src/prism/, or when adding async trading, analysis, or MCP code.
---

# PRISM-INSIGHT Python conventions

## Async

```python
# ✅
async with AsyncTradingContext(mode="demo") as trader:
    result = await trader.async_buy_stock(ticker)

# ❌ blocks event loop
requests.get(url)
```

## Sequential LLM sections

Do not parallelize report agents with `asyncio.gather` — rate limits and ordering matter.

```python
for section in sections:
    report = await generate_report(agent, section)
```

## KIS numeric fields

```python
from prism.trading.stock_trading import _safe_float, _safe_int
price = _safe_float(data.get("last"))
```

## Credentials

Never commit `.env`, `mcp_agent.secrets.yaml`, or `src/prism/trading/config/kis_devlp.yaml`.
