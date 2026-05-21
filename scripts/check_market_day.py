#!/usr/bin/env python3
"""
US Stock Market Business Day Checker (CLI wrapper).

Library functions live in ``cores.market_calendar``; this module re-exports
them for backward compatibility and provides the CLI entry point.

Exit code 0 → trading day, 1 → not a trading day.
"""

import sys
from datetime import date
from pathlib import Path

_repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_repo))

# Re-export every public helper so existing ``from scripts.check_market_day import …`` keeps working.
from cores.market_calendar import (  # noqa: F401, E402
    EST,
    KST,
    NYSE_CALENDAR,
    get_holiday_name,
    get_last_trading_day,
    get_market_status,
    get_next_trading_day,
    get_reference_date,
    is_market_open,
    is_us_market_day,
)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check US market trading day status")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed status")
    parser.add_argument("--date", "-d", type=str, help="Check specific date (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.date:
        check_date = date.fromisoformat(args.date)
        is_trading = is_us_market_day(check_date)
        if args.verbose:
            print(f"Date: {check_date}")
            print(f"Is trading day: {is_trading}")
            if not is_trading:
                print(f"Reason: {get_holiday_name(check_date) or 'Weekend'}")
        sys.exit(0 if is_trading else 1)
    else:
        if args.verbose:
            status = get_market_status()
            print("=== US Market Status ===")
            for key, value in status.items():
                print(f"{key}: {value}")

        if is_us_market_day():
            sys.exit(0)
        else:
            sys.exit(1)
