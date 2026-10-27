"""Trainer profiles, schedules and clients (Ф-3)."""

from fastapi import APIRouter, status

from app.api.deps import (
    ADMIN_ONLY,
    CurrentUser,
    Pagination,
    TrainerServiceDep,
    ensure_can_view_trainer_clients,
)
from app.api.errors import ERROR_RESPONSES
from app.schemas.clients import ClientShort
from app.schemas.common import Page
from app.schemas.trainers import TrainerCreate, TrainerRead, TrainerUpdate

router = APIRouter(prefix="/trainers", tags=["Тренери"], responses=ERROR_RESPONSES)


@router.get("", summary="Список тренерів (публічно)")
def list_trainers(service: TrainerServiceDep, page: Pagination) -> Page[TrainerRead]:
    items, total = service.page(offset=page.offset, limit=page.limit)
    return Page(items=[TrainerRead.from_model(t) for t in items], total=total, **page.model_dump())


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Додати тренера з графіком роботи (адміністратор)",
    dependencies=ADMIN_ONLY,
)
def create_trainer(data: TrainerCreate, service: TrainerServiceDep) -> TrainerRead:
    return TrainerRead.from_model(service.create(data))


@router.get("/{trainer_id}", summary="Профіль тренера (публічно)")
def get_trainer(trainer_id: int, service: TrainerServiceDep) -> TrainerRead:
    return TrainerRead.from_model(service.get(trainer_id))


@router.patch(
    "/{trainer_id}", summary="Змінити профіль або графік роботи (адміністратор)", dependencies=ADMIN_ONLY
)
def update_trainer(trainer_id: int, data: TrainerUpdate, service: TrainerServiceDep) -> TrainerRead:
    return TrainerRead.from_model(service.update(trainer_id, data))


@router.delete(
    "/{trainer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити тренера (адміністратор)",
    dependencies=ADMIN_ONLY,
)
def delete_trainer(trainer_id: int, service: TrainerServiceDep) -> None:
    service.delete(trainer_id)


@router.get("/{trainer_id}/clients", summary="Клієнти тренера (персонал або сам тренер)")
def trainer_clients(trainer_id: int, user: CurrentUser, service: TrainerServiceDep) -> list[ClientShort]:
    ensure_can_view_trainer_clients(user, trainer_id)
    return [ClientShort.model_validate(c) for c in service.clients(trainer_id)]
