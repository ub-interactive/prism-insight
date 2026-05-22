#!/usr/bin/env python3
"""
One-shot migration to US-only canonical table names.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


TABLE_RENAMES = [
    ("us_stock_holdings", "stock_holdings"),
    ("us_trading_history", "trading_history"),
    ("us_watchlist_history", "watchlist_history"),
    ("us_analysis_performance_tracker", "analysis_performance_tracker"),
    ("us_holding_decisions", "holding_decisions"),
    ("us_pending_orders", "pending_orders"),
    ("us_portfolio_adjustment_log", "portfolio_adjustment_log"),
]


def table_exists(cursor, table_name: str) -> bool:
    cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None


def run(db_path: Path, dry_run: bool) -> None:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    try:
        for old_name, new_name in TABLE_RENAMES:
            old_exists = table_exists(cursor, old_name)
            new_exists = table_exists(cursor, new_name)

            if not old_exists:
                print(f"[SKIP] {old_name}: table not found")
                continue

            if new_exists:
                print(f"[DROP] {new_name}: removing existing table before rename")
                if not dry_run:
                    cursor.execute(f"DROP TABLE IF EXISTS {new_name}")

            print(f"[RENAME] {old_name} -> {new_name}")
            if not dry_run:
                cursor.execute(f"ALTER TABLE {old_name} RENAME TO {new_name}")

        if not dry_run:
            conn.commit()
            print("[DONE] Migration committed")
        else:
            print("[DRY-RUN] No changes committed")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate us_* tables to canonical US-only names.")
    parser.add_argument(
        "--db-path",
        default=str(Path(__file__).resolve().parent.parent / "stock_tracking_db.sqlite"),
        help="Path to sqlite database file",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned operations only")
    args = parser.parse_args()
    run(Path(args.db_path), args.dry_run)


if __name__ == "__main__":
    main()
