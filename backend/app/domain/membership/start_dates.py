"""Which days a new membership may start on (Ф-5).

A membership must not start on a day it cannot be used: a day the club does not work, or today after
closing time (a single visit bought at 23:00 "for today" would be lost). The choice is limited to one
calendar month from the first usable day.
"""

from datetime import date, datetime, time, timedelta

from app.domain.membership.factories import add_months

START_WINDOW_MONTHS = 1


def _closing(opening_hours: dict[str, list[str]], day: date) -> time | None:
    """Closing time on that weekday, or None if the club does not work ("0" = Monday)."""
    hours = opening_hours.get(str(day.weekday()))
    return time.fromisoformat(hours[1]) if hours else None


def is_usable_start(opening_hours: dict[str, list[str]], day: date, now: datetime) -> bool:
    """The club works that day and, if it is today, has not closed yet."""
    closes = _closing(opening_hours, day)
    if closes is None:
        return False
    return day > now.date() or now.time() < closes


def start_options(opening_hours: dict[str, list[str]], now: datetime, not_before: date) -> list[date]:
    """Allowed start dates: usable days from the first usable one (not earlier than `not_before`,
    e.g. the day after a running membership) up to one calendar month after it."""
    first = max(now.date(), not_before)
    horizon = add_months(first, START_WINDOW_MONTHS + 1)  # a club closed for a while still gets a window
    earliest = next(
        (d for d in _days(first, horizon) if is_usable_start(opening_hours, d, now)),
        None,
    )
    if earliest is None:
        return []
    latest = add_months(earliest, START_WINDOW_MONTHS)
    return [d for d in _days(earliest, latest + timedelta(days=1)) if is_usable_start(opening_hours, d, now)]


def _days(start: date, stop: date):
    day = start
    while day < stop:
        yield day
        day += timedelta(days=1)
