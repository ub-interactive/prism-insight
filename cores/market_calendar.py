"""
US Stock Market calendar utilities.

Pure library functions for NYSE/NASDAQ trading-day detection using
pandas-market-calendars.  No CLI entry point, no logging side effects.

Consumers:
    - cores/data/surge_detector.py
    - reporting/report_generator.py
    - scripts/check_market_day.py  (CLI wrapper — re-exports these helpers)
"""

import logging
from datetime import date, datetime, timedelta

import pandas_market_calendars as mcal
import pytz

logger = logging.getLogger(__name__)

NYSE_CALENDAR = mcal.get_calendar("NYSE")

EST = pytz.timezone("America/New_York")
KST = pytz.timezone("Asia/Seoul")


def is_us_market_day(check_date: date | None = None) -> bool:
    """Return True if *check_date* (default: today EST) is a NYSE trading day."""
    if check_date is None:
        check_date = datetime.now(EST).date()

    if check_date.weekday() >= 5:
        return False

    fmt = check_date.strftime("%Y-%m-%d")
    return len(NYSE_CALENDAR.valid_days(start_date=fmt, end_date=fmt)) > 0


def get_holiday_name(check_date: date | None = None) -> str:
    """Holiday label for *check_date*, or empty string if not a holiday."""
    import pandas as pd

    if check_date is None:
        check_date = datetime.now(EST).date()

    for hd in NYSE_CALENDAR.holidays().holidays:
        if pd.Timestamp(hd).date() == check_date:
            return "US Market Holiday"
    return ""


def get_next_trading_day(from_date: date | None = None) -> date | None:
    """Next NYSE trading day strictly after *from_date*."""
    if from_date is None:
        from_date = datetime.now(EST).date()

    start = from_date.strftime("%Y-%m-%d")
    end = (from_date + timedelta(days=31)).strftime("%Y-%m-%d")

    for day in NYSE_CALENDAR.valid_days(start_date=start, end_date=end):
        if day.date() > from_date:
            return day.date()
    return None


def get_last_trading_day(from_date: date | None = None) -> date | None:
    """Most recent NYSE trading day on or before *from_date*."""
    if from_date is None:
        from_date = datetime.now(EST).date()

    if is_us_market_day(from_date):
        return from_date

    start = (from_date - timedelta(days=10)).strftime("%Y-%m-%d")
    end = from_date.strftime("%Y-%m-%d")
    valid_days = NYSE_CALENDAR.valid_days(start_date=start, end_date=end)
    return valid_days[-1].date() if len(valid_days) > 0 else None


def get_reference_date(from_date: date | None = None) -> str | None:
    """Last trading day as *YYYYMMDD* string (for analysis lookups)."""
    last = get_last_trading_day(from_date)
    return last.strftime("%Y%m%d") if last else None


def is_market_open() -> bool:
    """True when NYSE is in regular-hours session right now."""
    now_est = datetime.now(EST)
    if not is_us_market_day(now_est.date()):
        return False
    market_open = now_est.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_est.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= now_est <= market_close


def get_market_status() -> dict:
    """Comprehensive snapshot: open/closed, times, next trading day."""
    now_est = datetime.now(EST)
    now_kst = datetime.now(KST)
    today = now_est.date()

    is_trading_day = is_us_market_day(today)
    is_open = is_market_open()

    status = {
        "current_time_est": now_est.strftime("%Y-%m-%d %H:%M:%S EST"),
        "current_time_kst": now_kst.strftime("%Y-%m-%d %H:%M:%S KST"),
        "is_trading_day": is_trading_day,
        "is_market_open": is_open,
        "market_hours_est": "09:30-16:00",
        "market_hours_kst": "23:30-06:00 (next day)",
    }

    if not is_trading_day:
        status["reason"] = get_holiday_name(today) or "Weekend"
        status["next_trading_day"] = str(get_next_trading_day(today))

    return status
