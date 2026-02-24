"""US equity market session helpers (NYSE regular session)."""

from datetime import date, datetime, time, timedelta
from typing import Optional, Set
from zoneinfo import ZoneInfo


EASTERN_TZ = ZoneInfo("America/New_York")
REGULAR_OPEN = time(hour=9, minute=30)
REGULAR_CLOSE = time(hour=16, minute=0)


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    first_day = date(year, month, 1)
    delta = (weekday - first_day.weekday()) % 7
    return first_day + timedelta(days=delta + (n - 1) * 7)


def _last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    current = next_month - timedelta(days=1)
    while current.weekday() != weekday:
        current -= timedelta(days=1)
    return current


def _observed_holiday(day: date) -> date:
    if day.weekday() == 5:  # Saturday -> Friday
        return day - timedelta(days=1)
    if day.weekday() == 6:  # Sunday -> Monday
        return day + timedelta(days=1)
    return day


def _easter_sunday(year: int) -> date:
    # Anonymous Gregorian algorithm
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def nyse_holidays(year: int) -> Set[date]:
    return {
        _observed_holiday(date(year, 1, 1)),  # New Year's Day
        _nth_weekday_of_month(year, 1, weekday=0, n=3),  # Martin Luther King Jr. Day
        _nth_weekday_of_month(year, 2, weekday=0, n=3),  # Presidents Day
        _easter_sunday(year) - timedelta(days=2),  # Good Friday
        _last_weekday_of_month(year, 5, weekday=0),  # Memorial Day
        _observed_holiday(date(year, 6, 19)),  # Juneteenth
        _observed_holiday(date(year, 7, 4)),  # Independence Day
        _nth_weekday_of_month(year, 9, weekday=0, n=1),  # Labor Day
        _nth_weekday_of_month(year, 11, weekday=3, n=4),  # Thanksgiving
        _observed_holiday(date(year, 12, 25)),  # Christmas
    }


def is_regular_market_session(now: Optional[datetime] = None) -> bool:
    current = now.astimezone(EASTERN_TZ) if now else datetime.now(EASTERN_TZ)
    if current.weekday() >= 5:
        return False

    if current.date() in nyse_holidays(current.year):
        return False

    local_time = current.time()
    return REGULAR_OPEN <= local_time < REGULAR_CLOSE
