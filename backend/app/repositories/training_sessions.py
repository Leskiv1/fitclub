from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.domain.models import (
    Booking,
    BookingAction,
    BookingStatus,
    Hall,
    SessionKind,
    TrainingSession,
)
from app.repositories.base import BaseRepository


class TrainingSessionRepository(BaseRepository[TrainingSession]):
    model = TrainingSession

    def in_period(
        self,
        start: datetime,
        end: datetime,
        *,
        kind: SessionKind | None = None,
        trainer_id: int | None = None,
        hall_id: int | None = None,
    ) -> Sequence[TrainingSession]:
        """Sessions that start within [start, end) — the schedule, with trainer, hall and bookings loaded."""
        query = (
            select(TrainingSession)
            .where(
                TrainingSession.start_at >= start,
                TrainingSession.start_at < end,
                TrainingSession.is_cancelled.is_(False),
            )
            .options(
                selectinload(TrainingSession.trainer),
                selectinload(TrainingSession.hall),
                selectinload(TrainingSession.bookings),
            )
            .order_by(TrainingSession.start_at, TrainingSession.id)
        )
        if kind is not None:
            query = query.where(TrainingSession.kind == kind)
        if trainer_id is not None:
            query = query.where(TrainingSession.trainer_id == trainer_id)
        if hall_id is not None:
            query = query.where(TrainingSession.hall_id == hall_id)
        return self.session.scalars(query).all()

    def get_for_update(self, session_id: int) -> TrainingSession | None:
        """Locks the session row: concurrent bookings of the last place are processed one by one."""
        return self.session.scalar(
            select(TrainingSession).where(TrainingSession.id == session_id).with_for_update()
        )

    def conflicts(
        self,
        start: datetime,
        end: datetime,
        *,
        trainer_id: int | None = None,
        hall_id: int | None = None,
        exclude_id: int | None = None,
    ) -> Sequence[TrainingSession]:
        """Active sessions of the given trainer and/or in the given hall that overlap [start, end)."""
        same = []
        if trainer_id is not None:
            same.append(TrainingSession.trainer_id == trainer_id)
        if hall_id is not None:
            same.append(TrainingSession.hall_id == hall_id)
        query = select(TrainingSession).where(
            TrainingSession.is_cancelled.is_(False),
            TrainingSession.start_at < end,
            TrainingSession.end_at > start,
            or_(*same),
        )
        if exclude_id is not None:
            query = query.where(TrainingSession.id != exclude_id)
        return self.session.scalars(query).all()

    def busy_hall_ids(self, start: datetime, end: datetime) -> set[int]:
        query = select(TrainingSession.hall_id).where(
            TrainingSession.is_cancelled.is_(False),
            TrainingSession.start_at < end,
            TrainingSession.end_at > start,
        )
        return set(self.session.scalars(query).all())

    def first_free_hall(self, start: datetime, end: datetime) -> Hall | None:
        """The largest hall free at that time (individual sessions do not need a particular hall)."""
        busy = self.busy_hall_ids(start, end)
        halls = self.session.scalars(select(Hall).order_by(Hall.capacity.desc(), Hall.id)).all()
        return next((hall for hall in halls if hall.id not in busy), None)


class BookingRepository(BaseRepository[Booking]):
    model = Booking

    def active_for(self, client_id: int, session_id: int) -> Booking | None:
        return self.session.scalar(
            select(Booking).where(
                Booking.client_id == client_id,
                Booking.session_id == session_id,
                Booking.status != BookingStatus.CANCELLED,
            )
        )

    def for_client(self, client_id: int, *, since: datetime | None = None) -> Sequence[Booking]:
        query = (
            select(Booking)
            .join(TrainingSession, Booking.session_id == TrainingSession.id)
            .where(Booking.client_id == client_id)
            .options(
                selectinload(Booking.session).selectinload(TrainingSession.trainer),
                selectinload(Booking.session).selectinload(TrainingSession.hall),
            )
            .order_by(TrainingSession.start_at)
        )
        if since is not None:
            query = query.where(TrainingSession.start_at >= since)
        return self.session.scalars(query).all()

    def for_session(self, session_id: int) -> Sequence[Booking]:
        query = (
            select(Booking)
            .where(Booking.session_id == session_id, Booking.status != BookingStatus.CANCELLED)
            .options(selectinload(Booking.client))
            .order_by(Booking.created_at)
        )
        return self.session.scalars(query).all()


class BookingActionRepository(BaseRepository[BookingAction]):
    model = BookingAction

    def last_not_undone(self, actor_user_id: int) -> BookingAction | None:
        """The user's latest action that can still be undone, locked against a double undo."""
        query = (
            select(BookingAction)
            .where(BookingAction.actor_user_id == actor_user_id, BookingAction.undone_at.is_(None))
            .order_by(BookingAction.created_at.desc(), BookingAction.id.desc())
            .limit(1)
            .with_for_update()
        )
        return self.session.scalar(query)
