"""FastAPI dependencies that build services for a request (one DB session per request)."""

from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import PageParams
from app.services.catalog import HallService, MembershipOptionService, TariffPlanService
from app.services.clients import ClientService
from app.services.trainers import TrainerService

DbSession = Annotated[Session, Depends(get_db)]


def get_page_params(
    offset: int = Query(0, ge=0, description="Скільки записів пропустити"),
    limit: int = Query(20, ge=1, le=100, description="Розмір сторінки"),
) -> PageParams:
    return PageParams(offset=offset, limit=limit)


def get_client_service(db: DbSession) -> ClientService:
    return ClientService(db)


def get_trainer_service(db: DbSession) -> TrainerService:
    return TrainerService(db)


def get_hall_service(db: DbSession) -> HallService:
    return HallService(db)


def get_tariff_service(db: DbSession) -> TariffPlanService:
    return TariffPlanService(db)


def get_option_service(db: DbSession) -> MembershipOptionService:
    return MembershipOptionService(db)


Pagination = Annotated[PageParams, Depends(get_page_params)]
ClientServiceDep = Annotated[ClientService, Depends(get_client_service)]
TrainerServiceDep = Annotated[TrainerService, Depends(get_trainer_service)]
HallServiceDep = Annotated[HallService, Depends(get_hall_service)]
TariffServiceDep = Annotated[TariffPlanService, Depends(get_tariff_service)]
OptionServiceDep = Annotated[MembershipOptionService, Depends(get_option_service)]
