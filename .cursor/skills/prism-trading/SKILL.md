---
name: prism-trading
description: >-
  Trading safety for PRISM-INSIGHT: demo default, portfolio limits, US reserved
  orders, multi-account KIS config, and DB tables. Use when editing
  src/prism/trading/, stock_tracking_agent, pending_order_batch, trigger_batch,
  or any buy/sell/order execution logic.
---

# PRISM-INSIGHT trading safety

- Default mode: **demo** unless the task explicitly requires live trading.
- `MAX_SLOTS = 10`, `MAX_SAME_SECTOR = 3`
- Stop-loss by trigger: intraday_surge -5%, volume_surge/default -7%

## US market closed

- Buy reserved orders need `limit_price`
- Sell: `limit_price` or `use_moo=True` (Market On Open)

```python
result = await trading.async_buy_stock(ticker=ticker, limit_price=current_price)
```

## Multi-account

Fan-out uses all entries in `src/prism/trading/config/kis_devlp.yaml`.

## Database

`stock_holdings`, `trading_history`, `pending_orders`, etc. — see `src/prism/tracking/db_schema.py`.
