import sqlite3
import sys
import types
from pathlib import Path

import pending_order_batch as pending_batch


class _FakeTrader:
    init_calls = []

    def __init__(self, mode="demo", buy_amount=None, auto_trading=None, account_name=None, product_code="01"):
        self.mode = mode
        self.account_name = account_name
        self.product_code = product_code
        type(self).init_calls.append(
            {"mode": mode, "account_name": account_name, "product_code": product_code}
        )

    def is_reserved_order_available(self):
        return True

    def buy_reserved_order(self, ticker, limit_price, buy_amount=None, exchange=None):
        return {"success": True, "message": f"buy:{ticker}:{self.account_name}"}


def test_pending_order_query_uses_canonical_table(tmp_path):
    db_path = tmp_path / "stock_tracking_db.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE pending_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_key TEXT NOT NULL,
            account_name TEXT,
            product_code TEXT,
            mode TEXT,
            ticker TEXT NOT NULL,
            order_type TEXT NOT NULL,
            limit_price REAL NOT NULL,
            buy_amount REAL,
            exchange TEXT,
            status TEXT DEFAULT 'pending',
            failure_reason TEXT,
            created_at TEXT NOT NULL,
            executed_at TEXT,
            order_result TEXT
        )
        """
    )
    conn.execute(
        """
        INSERT INTO pending_orders
        (account_key, account_name, product_code, mode, ticker, order_type, limit_price, buy_amount, exchange, status, created_at)
        VALUES ('vps:batch-account:01', 'batch-account', '03', 'real', 'AAPL', 'buy', 190.0, 500.0, 'NASD', 'pending', date('now'))
        """
    )
    conn.commit()

    rows = pending_batch.get_pending_orders(conn, today_str=conn.execute("SELECT date('now')").fetchone()[0])
    conn.close()

    assert len(rows) == 1
    assert rows[0]["ticker"] == "AAPL"


def test_pending_order_batch_processes_with_account_context(monkeypatch, tmp_path):
    db_path = tmp_path / "stock_tracking_db.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE pending_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_key TEXT NOT NULL,
            account_name TEXT,
            product_code TEXT,
            mode TEXT,
            ticker TEXT NOT NULL,
            order_type TEXT NOT NULL,
            limit_price REAL NOT NULL,
            buy_amount REAL,
            exchange TEXT,
            status TEXT DEFAULT 'pending',
            failure_reason TEXT,
            created_at TEXT NOT NULL,
            executed_at TEXT,
            order_result TEXT
        )
        """
    )
    conn.execute(
        """
        INSERT INTO pending_orders
        (account_key, account_name, product_code, mode, ticker, order_type, limit_price, buy_amount, exchange, status, created_at)
        VALUES ('vps:batch-account:01', 'batch-account', '03', 'real', 'AAPL', 'buy', 190.0, 500.0, 'NASD', 'pending', date('now'))
        """
    )
    conn.commit()
    conn.close()

    _FakeTrader.init_calls = []
    monkeypatch.setattr(pending_batch, "DB_PATH", Path(db_path))

    fake_trading_module = types.ModuleType("trading.stock_trading")
    fake_trading_module.USStockTrading = _FakeTrader
    monkeypatch.setitem(sys.modules, "trading.stock_trading", fake_trading_module)

    pending_batch.process_pending_orders(dry_run=False)

    conn = sqlite3.connect(str(db_path))
    status = conn.execute("SELECT status FROM pending_orders WHERE ticker='AAPL'").fetchone()[0]
    conn.close()

    assert status == "executed"
    assert any(call["account_name"] == "batch-account" for call in _FakeTrader.init_calls)
