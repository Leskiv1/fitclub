"""Check-in at the reception and visit history (Ф-2)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import STAFF_ONLY, ClockDep, CurrentUser, DbSession, Pagination, ensure_can_view_client
from app.api.errors import ERROR_RESPONSES
from app.schemas.common import Page
from app.schemas.visits import CheckInIn, TodayVisitRead, VisitRead
from app.services.check_in import CheckInFacade

router = APIRouter(tags=["Відвідування"], responses=ERROR_RESPONSES)


def get_check_in_facade(db: DbSession, clock: ClockDep) -> CheckInFacade:
    return CheckInFacade(db, clock)


CheckInFacadeDep = Annotated[CheckInFacade, Depends(get_check_in_facade)]


@router.post(
    "/check-ins",
    status_code=status.HTTP_201_CREATED,
    summary="Зареєструвати вхід клієнта (рецепція)",
    description="Відмова повертається як 422 з кодом причини: no_membership, membership_frozen, "
    "membership_pending, membership_expired, no_visits_left, club_closed, already_checked_in.",
    dependencies=STAFF_ONLY,
)
def check_in(data: CheckInIn, facade: CheckInFacadeDep) -> VisitRead:
    return VisitRead.from_model(facade.check_in(data.client_id), facade.clock.zone)


@router.get("/check-ins/today", summary="Хто прийшов сьогодні (рецепція)", dependencies=STAFF_ONLY)
def visits_today(facade: CheckInFacadeDep) -> list[TodayVisitRead]:
    return [TodayVisitRead.from_model(v, facade.clock.zone) for v in facade.visits_today()]


@router.get("/clients/{client_id}/visits", summary="Історія відвідувань клієнта")
def client_visits(
    client_id: int, user: CurrentUser, facade: CheckInFacadeDep, page: Pagination
) -> Page[VisitRead]:
    ensure_can_view_client(user, client_id)
    items, total = facade.history(client_id, offset=page.offset, limit=page.limit)
    return Page(
        items=[VisitRead.from_model(v, facade.clock.zone) for v in items], total=total, **page.model_dump()
    )
