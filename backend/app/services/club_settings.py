"""Club settings (ЗВ-7): a cached snapshot shared by the whole process and their editing."""

import time as monotonic_time
from dataclasses import dataclass
from datetime import datetime, time
from threading import Lock
from typing import Any

from sqlalchemy.orm import Session

from app.core.scheduler import scheduler
from app.core.singleton import SingletonMeta
from app.domain.models import ClubSettings
from app.domain.models.club_settings import is_open_at
from app.repositories.club_settings import ClubSettingsRepository


@dataclass(frozen=True)
class ClubSettingsSnapshot:
    """Immutable copy of the settings row: safe to share between threads and DB sessions."""

    opening_hours: dict[str, list[str]]
    expiry_warning_days: int
    daily_check_time: time
    notifications_enabled: bool
    currency: str

    @classmethod
    def from_model(cls, row: ClubSettings) -> ClubSettingsSnapshot:
        return cls(
            opening_hours={day: list(hours) for day, hours in row.opening_hours.items()},
            expiry_warning_days=row.expiry_warning_days,
            daily_check_time=row.daily_check_time,
            notifications_enabled=row.notifications_enabled,
            currency=row.currency,
        )

    def is_open(self, moment: datetime) -> bool:
        return is_open_at(self.opening_hours, moment)


class ClubSettingsCache(metaclass=SingletonMeta):
    """GoF: Singleton — the only holder of club settings in the process.

    Settings are read on every check-in and by the daily job; the cache keeps a snapshot for `ttl` seconds.
    A change made in this process resets it at once; other uvicorn workers see it after at most `ttl`.
    """

    ttl = 60.0

    def __init__(self) -> None:
        self._snapshot: ClubSettingsSnapshot | None = None
        self._loaded_at = 0.0
        self._lock = Lock()

    def get(self, session: Session) -> ClubSettingsSnapshot:
        with self._lock:
            expired = monotonic_time.monotonic() - self._loaded_at > self.ttl
            if self._snapshot is None or expired:
                self._snapshot = ClubSettingsSnapshot.from_model(ClubSettingsRepository(session).get())
                self._loaded_at = monotonic_time.monotonic()
            return self._snapshot

    def invalidate(self) -> None:
        with self._lock:
            self._snapshot = None


class ClubSettingsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = ClubSettingsRepository(session)

    def get(self) -> ClubSettings:
        return self.repository.get()

    def update(self, changes: dict[str, Any]) -> ClubSettings:
        settings = self.repository.get()
        for name, value in changes.items():
            setattr(settings, name, value)
        self.session.commit()
        ClubSettingsCache().invalidate()
        if "daily_check_time" in changes:
            scheduler.reschedule(settings.daily_check_time)
        return settings
