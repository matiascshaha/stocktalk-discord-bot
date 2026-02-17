from datetime import datetime
from zoneinfo import ZoneInfo

from src.trading.orders.market_hours import is_regular_market_session


EASTERN = ZoneInfo("America/New_York")


def test_regular_market_session_open_weekday_midday():
    assert is_regular_market_session(datetime(2026, 2, 17, 11, 0, 0, tzinfo=EASTERN)) is True


def test_regular_market_session_closed_holiday_midday():
    # 2026-02-16 is Presidents Day (NYSE holiday)
    assert is_regular_market_session(datetime(2026, 2, 16, 11, 0, 0, tzinfo=EASTERN)) is False


def test_regular_market_session_closed_after_hours():
    assert is_regular_market_session(datetime(2026, 2, 17, 19, 0, 0, tzinfo=EASTERN)) is False

