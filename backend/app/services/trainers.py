"""Trainer profiles with their work schedule and clients (Ф-3)."""

from typing import Any

from sqlalchemy.orm import Session

from app.domain.errors import ConflictError
from app.domain.models import Client, Role, Trainer, WorkShift
from app.repositories.trainers import TrainerRepository
from app.services.accounts import AccountRegistry
from app.services.crud import CrudService


class TrainerService(CrudService[Trainer]):
    """GoF: Template Method — ConcreteClass; a trainer is created together with a user account."""

    entity_name = "Тренер"
    repository: TrainerRepository

    def __init__(self, session: Session) -> None:
        super().__init__(session, TrainerRepository(session))
        self.accounts = AccountRegistry(session)

    def clients(self, trainer_id: int) -> list[Client]:
        return self.get(trainer_id).clients()

    def _build(self, values: dict[str, Any]) -> Trainer:
        user = self.accounts.new_user(values.pop("email"), values.pop("password"), Role.TRAINER)
        shifts = [WorkShift(**shift) for shift in values.pop("work_shifts")]
        return Trainer(user=user, work_shifts=shifts, **values)

    def _apply(self, entity: Trainer, changes: dict[str, Any]) -> None:
        email = changes.pop("email", None)
        if email is not None:
            self.accounts.ensure_email_free(email, current=entity.user)
            entity.user.email = email.lower()
        shifts = changes.pop("work_shifts", None)
        if shifts is not None:
            entity.work_shifts = [WorkShift(**shift) for shift in shifts]  # old ones are deleted (orphans)
        super()._apply(entity, changes)

    def _ensure_deletable(self, entity: Trainer) -> None:
        if self.repository.has_sessions(entity.id):
            raise ConflictError("Тренер має заняття в розкладі — видалити його не можна")

    def _remove(self, entity: Trainer) -> None:
        # the account and the work shifts are removed together with the trainer
        self.session.delete(entity)
        self.session.delete(entity.user)
        self.session.flush()
