from datetime import date

from prism.core.cn.market_calendar import get_reference_date, is_market_day


def test_weekend_not_trading_day():
    assert is_market_day(date(2026, 6, 6)) is False  # Saturday


def test_holiday_not_trading_day():
    assert is_market_day(date(2025, 10, 1)) is False  # National Day


def test_reference_date_returns_yyyymmdd_string():
    ref = get_reference_date(date(2026, 6, 6))  # Saturday -> prior Friday
    assert ref == "20260605"


def test_reference_date_skips_holiday():
    assert get_reference_date(date(2025, 10, 1)) == "20250930"
