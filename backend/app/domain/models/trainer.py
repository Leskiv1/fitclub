from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.models.enums import BookingStatus

if TYPE_CHECKING:
    from app.domain.models.client import Client
    from app.domain.models.training import TrainingSession
    from app.domain.models.user import User


class Trainer(Base):
    """Trainer profile (Ф-3): specialization, work schedule and clients."""

    __tablename__ = "trainers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name: Mapped[str] = mapped_column(String(150))
    specialization: Mapped[str] = mapped_column(String(150))
    bio: Mapped[str | None] = mapped_column(Text)
    photo_url: Mapped[str | None] = mapped_column(String(500))

    user: Mapped[User] = relationship(back_populates="trainer")
    work_shifts: Mapped[list[WorkShift]] = relationship(
        back_populates="trainer", cascade="all, delete-orphan", order_by="WorkShift.weekday"
    )
    sessions: Mapped[list[TrainingSession]] = relationship(back_populates="trainer")

    def clients(self) -> list[Client]:
        """Clients who have an active booking with this trainer."""
        unique = {
            booking.client.id: booking.client
            for session in self.sessions
            for booking in session.bookings
            if booking.status != BookingStatus.CANCELLED
        }
        return sorted(unique.values(), key=lambda client: client.full_name)

    def is_available(self, start: datetime, end: datetime) -> bool:
        """Works at this time and has no other session that overlaps it."""
        on_shift = any(shift.covers(start) and shift.covers(end) for shift in self.work_shifts)
        busy = any(session.overlaps(start, end) for session in self.sessions)
        return on_shift and not busy


class WorkShift(Base):
    """One working interval of a trainer on a given day of the week (0 = Monday)."""

    __tablename__ = "work_shifts"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6", name="weekday_range"),
        CheckConstraint("end_time > start_time", name="time_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trainer_id: Mapped[int] = mapped_column(ForeignKey("trainers.id", ondelete="CASCADE"), index=True)
    weekday: Mapped[int] = mapped_column(SmallInteger)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    trainer: Mapped[Trainer] = relationship(back_populates="work_shifts")

    def covers(self, moment: datetime) -> bool:
        return moment.weekday() == self.weekday and self.start_time <= moment.time() <= self.end_time
