"""Common create/read/update/delete workflow for catalog entities."""

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import Base
from app.domain.errors import ConflictError, NotFoundError
from app.repositories.base import BaseRepository


class CrudService[ModelT: Base]:
    """GoF: Template Method — AbstractClass.

    `create`, `update` and `delete` are template methods: the order of steps (find → check uniqueness →
    apply changes → check business rules → save → commit) is fixed here, while subclasses fill in the
    steps that differ: `unique_fields`, `_build`, `_apply`, `_validate`, `_ensure_deletable`, `_remove`.
    """

    entity_name = "Об'єкт"
    unique_fields: tuple[str, ...] = ()

    def __init__(self, session: Session, repository: BaseRepository[ModelT]) -> None:
        self.session = session
        self.repository = repository

    # --- template methods ---

    def get(self, entity_id: int) -> ModelT:
        entity = self.repository.get(entity_id)
        if entity is None:
            raise NotFoundError(self.entity_name, entity_id)
        return entity

    def page(self, *, offset: int, limit: int) -> tuple[Sequence[ModelT], int]:
        return self.repository.page(offset=offset, limit=limit)

    def create(self, data: BaseModel) -> ModelT:
        values = data.model_dump()
        self._check_unique(values)
        entity = self._build(values)
        self._validate(entity)
        self.repository.add(entity)
        self.session.commit()
        return entity

    def update(self, entity_id: int, data: BaseModel) -> ModelT:
        entity = self.get(entity_id)
        changes = data.model_dump(exclude_unset=True)
        self._check_unique(changes, current=entity)
        self._apply(entity, changes)
        self._validate(entity)
        self.session.flush()
        self.session.commit()
        return entity

    def delete(self, entity_id: int) -> None:
        entity = self.get(entity_id)
        self._ensure_deletable(entity)
        self._remove(entity)
        self.session.commit()

    # --- steps (hooks) that subclasses may override ---

    def _build(self, values: dict[str, Any]) -> ModelT:
        return self.repository.model(**values)

    def _apply(self, entity: ModelT, changes: dict[str, Any]) -> None:
        for field, value in changes.items():
            setattr(entity, field, value)

    def _validate(self, entity: ModelT) -> None:
        """Business rules that need the final state of the entity (after merging a partial update)."""

    def _ensure_deletable(self, entity: ModelT) -> None:
        """Raise ConflictError if other data still refers to the entity."""

    def _remove(self, entity: ModelT) -> None:
        self.repository.delete(entity)

    def _check_unique(self, values: dict[str, Any], current: ModelT | None = None) -> None:
        for field in self.unique_fields:
            if field not in values or values[field] is None:
                continue
            existing = self.repository.get_by(**{field: values[field]})
            if existing is not None and existing is not current:
                raise ConflictError(f"{self.entity_name} зі значенням «{values[field]}» вже існує")
