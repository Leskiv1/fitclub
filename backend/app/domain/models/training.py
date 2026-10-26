from __future__ import annotations

from datetime import datetime, timedelta, tzinfo
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func, literal_column
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.models.enums import BookingStatus, SessionKind, str_enum

if TYPE_CHECKING:
    from app.domain.models.booking import Booking
    from app.domain.models.hall import Hall
    from app.domain.models.trainer import Trainer


class TrainingSession(Base):
    """Abstract training session (Ф-4); group and individual sessions share one table."""

    __tablename__ = "training_sessions"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="time_order"),
        CheckConstraint(
            "kind <> 'group' OR (title IS NOT NULL AND max_participants > 0)", name="group_fields"
        ),
        # The database itself forbids double-booking a trainer or a hall, whatever code inserts the rows
        ExcludeConstraint(
            ("trainer_id", "="),
            (func.tstzrange(literal_column("start_at"), literal_column("end_at")), "&&"),
            name="ex_training_sessions_trainer_overlap",
            using="gist",
            where="NOT is_cancelled",
        ),
        ExcludeConstraint(
            ("hall_id", "="),
            (func.tstzrange(literal_column("start_at"), literal_column("end_at")), "&&"),
            name="ex_training_sessions_hall_overlap",
            using="gist",
            where="NOT is_cancelled",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[SessionKind] = mapped_column(str_enum(SessionKind))
    trainer_id: Mapped[int] = mapped_column(ForeignKey("trainers.id", ondelete="RESTRICT"), index=True)
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id", ondelete="RESTRICT"), index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_cancelled: Mapped[bool] = mapped_column(
        default=False, comment="A cancelled session no longer occupies the trainer and the hall"
    )

    trainer: Mapped[Trainer] = relationship(back_populates="sessions")
    hall: Mapped[Hall] = relationship(back_populates="sessions")
    bookings: Mapped[list[Booking]] = relationship(back_populates="session", cascade="all, delete-orphan")

    __mapper_args__ = {"polymorphic_on": "kind", "polymorphic_abstract": True}

    def capacity(self) -> int:
        raise NotImplementedError

    def active_bookings(self) -> list[Booking]:
        return [booking for booking in self.bookings if booking.status != BookingStatus.CANCELLED]

    def free_places(self) -> int:
        return max(0, self.capacity() - len(self.active_bookings()))

    def is_full(self) -> bool:
        return self.free_places() == 0

    def overlaps(self, start: datetime, end: datetime) -> bool:
        return not self.is_cancelled and self.start_at < end and start < self.end_at


class GroupSession(TrainingSession):
    """Group training by schedule with a limited number of participants."""

    title: Mapped[str | None] = mapped_column(String(150))
    max_participants: Mapped[int | None]

    __mapper_args__ = {"polymorphic_identity": SessionKind.GROUP}

    def capacity(self) -> int:
        return self.max_participants or 0

    def clone(self, days: int, zone: tzinfo) -> GroupSession:
        """GoF: Prototype — a copy of this session `days` later, without bookings.

        The shift is done on the club's wall clock: an 18:00 class stays at 18:00 even across a DST change.
        """
        start = self.start_at.astimezone(zone) + timedelta(days=days)
        return GroupSession(
            trainer_id=self.trainer_id,
            hall_id=self.hall_id,
            title=self.title,
            max_participants=self.max_participants,
            start_at=start,
            end_at=start + (self.end_at - self.start_at),
        )


class IndividualSession(TrainingSession):
    """Personal session of one client with a trainer."""

    __mapper_args__ = {"polymorphic_identity": SessionKind.INDIVIDUAL}

    def capacity(self) -> int:
        return 1
