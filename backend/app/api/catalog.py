"""Catalog endpoints: halls, tariff plans (Ф-5) and membership options."""

from fastapi import APIRouter, status

from app.api.deps import HallServiceDep, OptionServiceDep, Pagination, TariffServiceDep
from app.api.errors import ERROR_RESPONSES
from app.schemas.common import Page
from app.schemas.halls import HallCreate, HallRead, HallUpdate
from app.schemas.tariffs import (
    MembershipOptionCreate,
    MembershipOptionRead,
    MembershipOptionUpdate,
    TariffPlanCreate,
    TariffPlanRead,
    TariffPlanUpdate,
)

halls = APIRouter(prefix="/halls", tags=["Зали"], responses=ERROR_RESPONSES)
tariffs = APIRouter(prefix="/tariffs", tags=["Тарифи"], responses=ERROR_RESPONSES)
options = APIRouter(prefix="/membership-options", tags=["Опції абонемента"], responses=ERROR_RESPONSES)


# --- halls ---


@halls.get("", summary="Список залів")
def list_halls(service: HallServiceDep, page: Pagination) -> Page[HallRead]:
    items, total = service.page(offset=page.offset, limit=page.limit)
    return Page(items=[HallRead.model_validate(h) for h in items], total=total, **page.model_dump())


@halls.post("", status_code=status.HTTP_201_CREATED, summary="Додати зал")
def create_hall(data: HallCreate, service: HallServiceDep) -> HallRead:
    return HallRead.model_validate(service.create(data))


@halls.get("/{hall_id}", summary="Зал")
def get_hall(hall_id: int, service: HallServiceDep) -> HallRead:
    return HallRead.model_validate(service.get(hall_id))


@halls.patch("/{hall_id}", summary="Змінити зал")
def update_hall(hall_id: int, data: HallUpdate, service: HallServiceDep) -> HallRead:
    return HallRead.model_validate(service.update(hall_id, data))


@halls.delete("/{hall_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Видалити зал")
def delete_hall(hall_id: int, service: HallServiceDep) -> None:
    service.delete(hall_id)


# --- tariff plans ---


@tariffs.get("", summary="Список тарифних планів")
def list_tariffs(service: TariffServiceDep, page: Pagination) -> Page[TariffPlanRead]:
    items, total = service.page(offset=page.offset, limit=page.limit)
    return Page(items=[TariffPlanRead.model_validate(t) for t in items], total=total, **page.model_dump())


@tariffs.post("", status_code=status.HTTP_201_CREATED, summary="Створити тарифний план")
def create_tariff(data: TariffPlanCreate, service: TariffServiceDep) -> TariffPlanRead:
    return TariffPlanRead.model_validate(service.create(data))


@tariffs.get("/{tariff_id}", summary="Тарифний план")
def get_tariff(tariff_id: int, service: TariffServiceDep) -> TariffPlanRead:
    return TariffPlanRead.model_validate(service.get(tariff_id))


@tariffs.patch("/{tariff_id}", summary="Змінити тарифний план (зокрема деактивувати)")
def update_tariff(tariff_id: int, data: TariffPlanUpdate, service: TariffServiceDep) -> TariffPlanRead:
    return TariffPlanRead.model_validate(service.update(tariff_id, data))


@tariffs.delete("/{tariff_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Видалити тарифний план")
def delete_tariff(tariff_id: int, service: TariffServiceDep) -> None:
    service.delete(tariff_id)


# --- membership options ---


@options.get("", summary="Список додаткових опцій")
def list_options(service: OptionServiceDep, page: Pagination) -> Page[MembershipOptionRead]:
    items, total = service.page(offset=page.offset, limit=page.limit)
    return Page(
        items=[MembershipOptionRead.model_validate(o) for o in items], total=total, **page.model_dump()
    )


@options.post("", status_code=status.HTTP_201_CREATED, summary="Створити опцію")
def create_option(data: MembershipOptionCreate, service: OptionServiceDep) -> MembershipOptionRead:
    return MembershipOptionRead.model_validate(service.create(data))


@options.get("/{option_id}", summary="Опція")
def get_option(option_id: int, service: OptionServiceDep) -> MembershipOptionRead:
    return MembershipOptionRead.model_validate(service.get(option_id))


@options.patch("/{option_id}", summary="Змінити опцію")
def update_option(
    option_id: int, data: MembershipOptionUpdate, service: OptionServiceDep
) -> MembershipOptionRead:
    return MembershipOptionRead.model_validate(service.update(option_id, data))


@options.delete("/{option_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Видалити опцію")
def delete_option(option_id: int, service: OptionServiceDep) -> None:
    service.delete(option_id)
