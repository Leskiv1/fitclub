"""Current time in the club's time zone.

Opening hours and "today" are local notions, so every business rule that depends on the time asks the clock
instead of calling datetime.now() directly; tests replace the clock with a fixed one.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


class Clock:
    def __init__(self, timezone: str | None = None) -> None:
        self.zone = ZoneInfo(timezone or get_settings().club_timezone)

    def now(self) -> datetime:
        return datetime.now(self.zone)

    def today(self) -> date:
        return self.now().date()


class FixedClock(Clock):
    """A clock that always shows the given moment (for tests and reproducible scenarios)."""

    def __init__(self, moment: datetime) -> None:
        super().__init__()
        self.moment = moment.astimezone(self.zone)

    def now(self) -> datetime:
        return self.moment
