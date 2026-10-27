from __future__ import annotations

from datetime import datetime, time

from sqlalchemy import JSON, CheckConstraint, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def is_open_at(opening_hours: dict[str, list[str]], moment: datetime) -> bool:
    """opening_hours maps a weekday ("0" = Monday) to ["HH:MM", "HH:MM"]; a missing day means closed."""
    hours = opening_hours.get(str(moment.weekday()))
    if not hours:
        return False
    opens, closes = (time.fromisoformat(value) for value in hours)
    return opens <= moment.time() <= closes


class ClubSettings(Base):
    """Club-wide settings; the table always holds exactly one row (id = 1)."""

    __tablename__ = "club_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="single_row"),
        CheckConstraint("expiry_warning_days >= 0", name="warning_days_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    opening_hours: Mapped[dict[str, list[str]]] = mapped_column(JSON)
    expiry_warning_days: Mapped[int] = mapped_column(default=7)
    daily_check_time: Mapped[time] = mapped_column(Time, default=time(9, 0))
    notifications_enabled: Mapped[bool] = mapped_column(default=True)
    currency: Mapped[str] = mapped_column(String(3), default="UAH")

    def is_open(self, moment: datetime) -> bool:
        return is_open_at(self.opening_hours, moment)
