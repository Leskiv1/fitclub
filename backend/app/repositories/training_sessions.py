from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select

from app.domain.models import TrainingSession
from app.repositories.base import BaseRepository


class TrainingSessionRepository(BaseRepository[TrainingSession]):
    model = TrainingSession

    def in_period(self, start: datetime, end: datetime) -> Sequence[TrainingSession]:
        """Sessions that start within [start, end) — used for the weekly schedule."""
        query = (
            select(TrainingSession)
            .where(TrainingSession.start_at >= start, TrainingSession.start_at < end)
            .order_by(TrainingSession.start_at)
        )
        return self.session.scalars(query).all()
