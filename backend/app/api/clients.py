"""Client registry endpoints (Ф-1)."""

from fastapi import APIRouter, Query, status

from app.api.deps import ClientServiceDep, Pagination
from app.api.errors import ERROR_RESPONSES
from app.schemas.clients import ClientCreate, ClientRead, ClientUpdate
from app.schemas.common import Page

router = APIRouter(prefix="/clients", tags=["Клієнти"], responses=ERROR_RESPONSES)


@router.get("", summary="Список клієнтів з пошуком")
def list_clients(
    service: ClientServiceDep,
    page: Pagination,
    q: str | None = Query(None, max_length=100, description="Частина ПІБ або телефону"),
) -> Page[ClientRead]:
    items, total = service.search(q, offset=page.offset, limit=page.limit)
    return Page(items=[ClientRead.from_model(c) for c in items], total=total, **page.model_dump())


@router.post("", status_code=status.HTTP_201_CREATED, summary="Зареєструвати клієнта")
def create_client(data: ClientCreate, service: ClientServiceDep) -> ClientRead:
    return ClientRead.from_model(service.create(data))


@router.get("/{client_id}", summary="Картка клієнта")
def get_client(client_id: int, service: ClientServiceDep) -> ClientRead:
    return ClientRead.from_model(service.get(client_id))


@router.patch("/{client_id}", summary="Змінити дані клієнта")
def update_client(client_id: int, data: ClientUpdate, service: ClientServiceDep) -> ClientRead:
    return ClientRead.from_model(service.update(client_id, data))


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Видалити клієнта")
def delete_client(client_id: int, service: ClientServiceDep) -> None:
    service.delete(client_id)
