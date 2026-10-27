"""Notifications (Ф-6): log for the administrator, feed of a client, manual run of the daily check."""

from fastapi import APIRouter

from app.api.deps import (
    ADMIN_ONLY,
    ClockDep,
    CurrentUser,
    DbSession,
    EventBusDep,
    Pagination,
    ensure_can_view_client,
)
from app.api.errors import ERROR_RESPONSES
from app.domain.models import NotificationKind, NotificationStatus
from app.repositories.notifications import NotificationRepository
from app.schemas.common import Page
from app.schemas.notifications import DailyCheckOut, NotificationRead
from app.services.notifications.daily_check import ExpiringMembershipsJob

router = APIRouter(tags=["Сповіщення"], responses=ERROR_RESPONSES)


@router.get("/notifications", summary="Журнал сповіщень (адміністратор)", dependencies=ADMIN_ONLY)
def notification_log(
    db: DbSession,
    clock: ClockDep,
    page: Pagination,
    client_id: int | None = None,
    kind: NotificationKind | None = None,
    status: NotificationStatus | None = None,
) -> Page[NotificationRead]:
    items, total = NotificationRepository(db).search(
        client_id=client_id, kind=kind, status=status, offset=page.offset, limit=page.limit
    )
    return Page(
        items=[NotificationRead.from_model(n, clock.zone) for n in items], total=total, **page.model_dump()
    )


@router.get("/clients/{client_id}/notifications", summary="Сповіщення клієнта")
def client_notifications(
    client_id: int, user: CurrentUser, db: DbSession, clock: ClockDep, page: Pagination
) -> Page[NotificationRead]:
    ensure_can_view_client(user, client_id)
    items, total = NotificationRepository(db).search(
        client_id=client_id, offset=page.offset, limit=page.limit
    )
    return Page(
        items=[NotificationRead.from_model(n, clock.zone) for n in items], total=total, **page.model_dump()
    )


@router.post(
    "/notifications/run-check",
    summary="Виконати щоденну перевірку абонементів зараз (адміністратор)",
    dependencies=ADMIN_ONLY,
)
def run_daily_check_now(db: DbSession, clock: ClockDep, events: EventBusDep) -> DailyCheckOut:
    result = ExpiringMembershipsJob(db, clock, events).run()
    return DailyCheckOut(expired=result.expired, reminders=result.reminders, skipped=result.skipped)
