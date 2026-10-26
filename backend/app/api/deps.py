"""FastAPI dependencies: DB session, current user, role checks and services for a request."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.database import get_db
from app.domain.errors import AuthenticationError, PermissionDeniedError
from app.domain.models import Role, User
from app.schemas.common import PageParams
from app.services.auth import AuthService
from app.services.catalog import HallService, MembershipOptionService, TariffPlanService
from app.services.clients import ClientService
from app.services.trainers import TrainerService

DbSession = Annotated[Session, Depends(get_db)]


def get_clock() -> Clock:
    """Current time of the club; replaced by a fixed clock in tests."""
    return Clock()


ClockDep = Annotated[Clock, Depends(get_clock)]

# auto_error=False: a missing token is reported in our own error format, not FastAPI's default one
bearer_scheme = HTTPBearer(auto_error=False, description="JWT з POST /api/auth/login")


def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(db)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Потрібно увійти в систему")
    return auth.user_from_token(credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[[User], User]:
    """Dependency factory: lets the request through only for users with one of the given roles."""

    def check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise PermissionDeniedError()
        return user

    return check


ADMIN_ONLY = [Depends(require_roles(Role.ADMIN))]
STAFF_ONLY = [Depends(require_roles(Role.RECEPTION, Role.ADMIN))]
STAFF_ROLES = (Role.RECEPTION, Role.ADMIN)


def ensure_can_view_client(user: User, client_id: int) -> None:
    """Staff see any client; a client sees only their own card.

    Checked before loading the client, so a foreign id gives 403 whether it exists or not.
    """
    if user.role in STAFF_ROLES:
        return
    if user.role == Role.CLIENT and user.client is not None and user.client.id == client_id:
        return
    raise PermissionDeniedError()


def ensure_can_view_trainer_clients(user: User, trainer_id: int) -> None:
    """Staff see the clients of any trainer; a trainer sees only their own clients."""
    if user.role in STAFF_ROLES:
        return
    if user.role == Role.TRAINER and user.trainer is not None and user.trainer.id == trainer_id:
        return
    raise PermissionDeniedError()


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
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ClientServiceDep = Annotated[ClientService, Depends(get_client_service)]
TrainerServiceDep = Annotated[TrainerService, Depends(get_trainer_service)]
HallServiceDep = Annotated[HallService, Depends(get_hall_service)]
TariffServiceDep = Annotated[TariffPlanService, Depends(get_tariff_service)]
OptionServiceDep = Annotated[MembershipOptionService, Depends(get_option_service)]
