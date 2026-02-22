from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.trading.orders.market_hours import is_regular_market_session
from src.trading.orders.market_hours import (
    _easter_sunday,
    _last_weekday_of_month,
    _nth_weekday_of_month,
    _observed_holiday,
    nyse_holidays,
)


EASTERN = ZoneInfo("America/New_York")
pytestmark = [pytest.mark.unit]


def test_regular_market_session_open_weekday_midday():
    assert is_regular_market_session(datetime(2026, 2, 17, 11, 0, 0, tzinfo=EASTERN)) is True


def test_regular_market_session_closed_holiday_midday():
    # 2026-02-16 is Presidents Day (NYSE holiday)
    assert is_regular_market_session(datetime(2026, 2, 16, 11, 0, 0, tzinfo=EASTERN)) is False


def test_regular_market_session_closed_after_hours():
    assert is_regular_market_session(datetime(2026, 2, 17, 19, 0, 0, tzinfo=EASTERN)) is False


def test_nth_weekday_of_month_returns_expected_monday():
    assert _nth_weekday_of_month(2026, 2, weekday=0, n=3).isoformat() == "2026-02-16"


def test_last_weekday_of_month_returns_expected_monday():
    assert _last_weekday_of_month(2026, 5, weekday=0).isoformat() == "2026-05-25"


def test_observed_holiday_saturday_moves_to_friday():
    assert _observed_holiday(datetime(2026, 7, 4).date()).isoformat() == "2026-07-03"


def test_observed_holiday_sunday_moves_to_monday():
    assert _observed_holiday(datetime(2027, 7, 4).date()).isoformat() == "2027-07-05"


def test_observed_holiday_weekday_unchanged():
    assert _observed_holiday(datetime(2026, 12, 25).date()).isoformat() == "2026-12-25"


def test_easter_sunday_returns_known_2026_date():
    assert _easter_sunday(2026).isoformat() == "2026-04-05"


def test_nyse_holidays_contains_core_dates():
    holidays = nyse_holidays(2026)
    assert datetime(2026, 1, 1).date() in holidays
    assert datetime(2026, 2, 16).date() in holidays
    assert datetime(2026, 4, 3).date() in holidays
    assert datetime(2026, 11, 26).date() in holidays
