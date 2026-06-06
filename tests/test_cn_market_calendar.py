from datetime import date

from prism.core.market_calendar_cn import get_cn_reference_date, is_cn_market_day


def test_weekend_not_trading_day():
    assert is_cn_market_day(date(2026, 6, 6)) is False  # Saturday


def test_reference_date_returns_yyyymmdd_string():
    ref = get_cn_reference_date(date(2026, 6, 6))
    assert len(ref) == 8
    assert ref.isdigit()
