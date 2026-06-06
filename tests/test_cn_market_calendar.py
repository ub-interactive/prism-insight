from datetime import date

from prism.core.market_calendar_cn import get_cn_reference_date, is_cn_market_day


def test_weekend_not_trading_day():
    assert is_cn_market_day(date(2026, 6, 6)) is False  # Saturday


def test_holiday_not_trading_day():
    assert is_cn_market_day(date(2025, 10, 1)) is False  # National Day


def test_reference_date_returns_yyyymmdd_string():
    ref = get_cn_reference_date(date(2026, 6, 6))  # Saturday -> prior Friday
    assert ref == "20260605"


def test_reference_date_skips_holiday():
    assert get_cn_reference_date(date(2025, 10, 1)) == "20250930"
