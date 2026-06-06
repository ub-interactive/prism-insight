"""China A-share market calendar utilities (SSE/SZSE shared holidays)."""

import logging
from datetime import date, datetime, timedelta

import pandas_market_calendars as mcal
import pytz

logger = logging.getLogger(__name__)

SSE_CALENDAR = mcal.get_calendar("SSE")
CST = pytz.timezone("Asia/Shanghai")


def is_cn_market_day(check_date: date | None = None) -> bool:
    """Return True if *check_date* (default: today CST) is an SSE trading day."""
    if check_date is None:
        check_date = datetime.now(CST).date()
    if check_date.weekday() >= 5:
        return False
    fmt = check_date.strftime("%Y-%m-%d")
    return len(SSE_CALENDAR.valid_days(start_date=fmt, end_date=fmt)) > 0


def get_last_trading_day(from_date: date | None = None) -> date:
    """Most recent SSE trading day on or before *from_date*."""
    if from_date is None:
        from_date = datetime.now(CST).date()
    start = (from_date - timedelta(days=14)).strftime("%Y-%m-%d")
    end = from_date.strftime("%Y-%m-%d")
    valid = SSE_CALENDAR.valid_days(start_date=start, end_date=end)
    if len(valid) == 0:
        return from_date
    last = valid[-1]
    return last.date() if hasattr(last, "date") else last.to_pydatetime().date()


def get_cn_reference_date(from_date: date | None = None) -> str:
    """Return last CN trading day as YYYYMMDD."""
    if from_date is None:
        from_date = datetime.now(CST).date()
    if is_cn_market_day(from_date):
        d = from_date
    else:
        d = get_last_trading_day(from_date)
    return d.strftime("%Y%m%d")
