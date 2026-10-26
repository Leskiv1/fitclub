from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domain.models import Trainer, TrainingSession
from app.repositories.base import BaseRepository


class TrainerRepository(BaseRepository[Trainer]):
    model = Trainer

    def page(self, *, offset: int = 0, limit: int = 100) -> tuple[Sequence[Trainer], int]:
        query = (
            select(Trainer)
            .options(selectinload(Trainer.user), selectinload(Trainer.work_shifts))
            .order_by(Trainer.full_name, Trainer.id)
        )
        return self._page(query, offset, limit)

    def has_sessions(self, trainer_id: int) -> bool:
        return self._exists(select(TrainingSession.id).where(TrainingSession.trainer_id == trainer_id))
