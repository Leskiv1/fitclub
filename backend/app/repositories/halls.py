from sqlalchemy import select

from app.domain.models import Hall, TrainingSession
from app.repositories.base import BaseRepository


class HallRepository(BaseRepository[Hall]):
    model = Hall

    def is_in_use(self, hall_id: int) -> bool:
        return self._exists(select(TrainingSession.id).where(TrainingSession.hall_id == hall_id))
