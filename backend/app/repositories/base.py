"""Generic repository: common data access operations shared by all repositories."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, exists, func, select
from sqlalchemy.orm import Session

from app.core.database import Base


class BaseRepository[ModelT: Base]:
    """Works with one model; subclasses set `model` and add their own queries.

    Repositories only flush changes — committing the transaction is the job of the service layer.
    """

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, entity_id: int) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def get_by(self, **filters: Any) -> ModelT | None:
        return self.session.scalar(select(self.model).filter_by(**filters).limit(1))

    def list(self, *, offset: int = 0, limit: int = 100) -> Sequence[ModelT]:
        query = select(self.model).order_by(self.model.id).offset(offset).limit(limit)
        return self.session.scalars(query).all()

    def page(self, *, offset: int = 0, limit: int = 100) -> tuple[Sequence[ModelT], int]:
        return self._page(select(self.model).order_by(self.model.id), offset, limit)

    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: ModelT) -> None:
        self.session.delete(entity)
        self.session.flush()

    def _page(self, query: Select, offset: int, limit: int) -> tuple[Sequence[ModelT], int]:
        """Items of one page plus the total number of rows matching the query."""
        total = self.session.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
        items = self.session.scalars(query.offset(offset).limit(limit)).all()
        return items, total or 0

    def _exists(self, query: Select) -> bool:
        return bool(self.session.scalar(select(exists(query))))
