"""US trigger reliability tests against canonical table names."""

import sqlite3

import pytest


@pytest.fixture
def us_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE analysis_performance_tracker (
            id INTEGER PRIMARY KEY,
            ticker TEXT NOT NULL,
            company_name TEXT NOT NULL,
            analysis_date TEXT NOT NULL,
            analysis_price REAL NOT NULL,
            trigger_type TEXT,
            return_30d REAL,
            tracking_status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE trading_history (
            id INTEGER PRIMARY KEY,
            account_key TEXT,
            ticker TEXT,
            company_name TEXT,
            trigger_type TEXT,
            profit_rate REAL,
            sell_date TEXT
        )
        """
    )

    for i in range(4):
        ret = 0.06 + i * 0.02 if i < 3 else -0.04
        c.execute(
            """
            INSERT INTO analysis_performance_tracker
            (ticker, company_name, analysis_date, analysis_price, trigger_type, return_30d, created_at)
            VALUES (?, 'Test Corp', '2026-01-01', 100.0, 'Gap Up Momentum Top', ?, datetime('now'))
            """,
            (f"TST{i}", ret),
        )

    for i in range(2):
        c.execute(
            """
            INSERT INTO analysis_performance_tracker
            (ticker, company_name, analysis_date, analysis_price, trigger_type, created_at)
            VALUES (?, 'Pending Corp', '2026-02-01', 50.0, 'Volume Surge Top', datetime('now'))
            """,
            (f"PND{i}",),
        )

    c.execute(
        """
        INSERT INTO trading_history
        (id, account_key, ticker, company_name, trigger_type, profit_rate, sell_date)
        VALUES
        (1, 'vps:us-primary:01', 'AAPL', 'Apple Inc.', 'Gap Up Momentum Top', 8.0, '2026-03-01'),
        (2, 'vps:us-primary:01', 'MSFT', 'Microsoft Corp.', 'Gap Up Momentum Top', -5.0, '2026-03-02')
        """
    )

    conn.commit()
    yield conn
    conn.close()


def test_us_trigger_reliability_structure(us_db):
    from examples.generate_us_dashboard_json import USDashboardDataGenerator

    gen = USDashboardDataGenerator.__new__(USDashboardDataGenerator)
    gen._primary_account_key = "vps:us-primary:01"
    result = gen.get_us_trigger_reliability(us_db)

    assert "trigger_reliability" in result
    assert "best_trigger" in result
    assert "last_updated" in result
    assert len(result["trigger_reliability"]) > 0


def test_us_trigger_reliability_grade_and_counts(us_db):
    from examples.generate_us_dashboard_json import USDashboardDataGenerator

    gen = USDashboardDataGenerator.__new__(USDashboardDataGenerator)
    gen._primary_account_key = "vps:us-primary:01"
    result = gen.get_us_trigger_reliability(us_db)

    gap = next(
        (row for row in result["trigger_reliability"] if row["trigger_type"] == "Gap Up Momentum Top"),
        None,
    )
    assert gap is not None
    assert gap["analysis_accuracy"]["completed"] == 4
    assert gap["actual_trading"]["count"] == 2
    assert gap["grade"] in {"A", "B", "C", "D"}


def test_us_dashboard_caches_primary_account_key(monkeypatch):
    import examples.generate_us_dashboard_json as dashboard_module
    from examples.generate_us_dashboard_json import USDashboardDataGenerator

    calls = []

    def fake_resolve_account(*, svr, market):
        calls.append((svr, market))
        return {"account_key": "vps:us-primary:01"}

    monkeypatch.setitem(dashboard_module._cfg, "default_mode", "demo")
    monkeypatch.setattr(dashboard_module.ka, "resolve_account", fake_resolve_account)

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE stock_holdings (
            account_key TEXT,
            ticker TEXT,
            company_name TEXT,
            buy_price REAL,
            buy_date TEXT,
            current_price REAL,
            last_updated TEXT,
            scenario TEXT,
            target_price REAL,
            stop_loss REAL,
            trigger_type TEXT,
            trigger_mode TEXT,
            sector TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE trading_history (
            id INTEGER PRIMARY KEY,
            account_key TEXT,
            ticker TEXT,
            company_name TEXT,
            buy_price REAL,
            buy_date TEXT,
            sell_price REAL,
            sell_date TEXT,
            profit_rate REAL,
            holding_days INTEGER,
            scenario TEXT,
            trigger_type TEXT,
            trigger_mode TEXT,
            sector TEXT
        )
        """
    )
    conn.execute(
        """
        INSERT INTO stock_holdings (
            account_key, ticker, company_name, buy_price, buy_date, current_price,
            last_updated, scenario, target_price, stop_loss, trigger_type, trigger_mode, sector
        )
        VALUES (
            'vps:us-primary:01', 'AAPL', 'Apple Inc.', 180.5, '2026-03-01',
            185.0, '2026-03-02 09:00:00', '{}', 200.0, 170.0, 'gap_up', 'morning', 'Technology'
        )
        """
    )
    conn.execute(
        """
        INSERT INTO trading_history (
            id, account_key, ticker, company_name, buy_price, buy_date, sell_price,
            sell_date, profit_rate, holding_days, scenario, trigger_type, trigger_mode, sector
        )
        VALUES (
            1, 'vps:us-primary:01', 'AAPL', 'Apple Inc.', 180.5, '2026-03-01',
            190.0, '2026-03-10', 5.26, 9, '{}', 'gap_up', 'morning', 'Technology'
        )
        """
    )
    conn.commit()

    generator = USDashboardDataGenerator(
        db_path=":memory:",
        output_path="dummy.json",
        enable_translation=False,
    )

    holdings = generator.get_us_stock_holdings(conn)
    history = generator.get_us_trading_history(conn)

    assert len(holdings) == 1
    assert len(history) == 1
    assert calls == [("vps", "us")]
    conn.close()
