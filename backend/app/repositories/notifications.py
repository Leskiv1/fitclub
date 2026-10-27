from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domain.models import Notification, NotificationKind, NotificationStatus
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    def search(
        self,
        *,
        client_id: int | None = None,
        kind: NotificationKind | None = None,
        status: NotificationStatus | None = None,
        offset: int,
        limit: int,
    ) -> tuple[Sequence[Notification], int]:
        """Notification log, newest first."""
        query = (
            select(Notification)
            .options(selectinload(Notification.client))
            .order_by(Notification.created_at.desc(), Notification.id.desc())
        )
        if client_id is not None:
            query = query.where(Notification.client_id == client_id)
        if kind is not None:
            query = query.where(Notification.kind == kind)
        if status is not None:
            query = query.where(Notification.status == status)
        return self._page(query, offset, limit)
