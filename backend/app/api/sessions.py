"""Schedule of training sessions (Ф-4) and free slots of trainers."""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import ADMIN_ONLY, STAFF_ROLES, ClockDep, CurrentUser, DbSession
from app.api.errors import ERROR_RESPONSES
from app.domain.errors import PermissionDeniedError
from app.domain.models import Role, SessionKind
from app.schemas.sessions import (
    CopyWeekIn,
    CopyWeekOut,
    GroupSessionCreate,
    GroupSessionUpdate,
    ParticipantRead,
    SessionRead,
    SkippedSession,
)
from app.services.bookings import BookingFacade
from app.services.schedule import ScheduleService

router = APIRouter(tags=["Розклад"], responses=ERROR_RESPONSES)


def get_schedule_service(db: DbSession, clock: ClockDep) -> ScheduleService:
    return ScheduleService(db, clock)


ScheduleDep = Annotated[ScheduleService, Depends(get_schedule_service)]


@router.get("/sessions", summary="Розклад на тиждень (публічно)")
def list_sessions(
    service: ScheduleDep,
    week: Annotated[
        date | None, Query(description="Будь-яка дата тижня; за замовчуванням — поточний тиждень")
    ] = None,
    kind: SessionKind | None = None,
    trainer_id: int | None = None,
) -> list[SessionRead]:
    day = week or service.clock.today()
    monday = day - timedelta(days=day.weekday())
    sessions = service.week(monday, kind=kind, trainer_id=trainer_id)
    return [SessionRead.from_model(s, service.clock.zone) for s in sessions]


@router.get("/sessions/{session_id}", summary="Заняття з кількістю вільних місць (публічно)")
def get_session(session_id: int, service: ScheduleDep) -> SessionRead:
    return SessionRead.from_model(service.get(session_id), service.clock.zone)


@router.post(
    "/sessions",
    status_code=status.HTTP_201_CREATED,
    summary="Додати групове заняття (адміністратор)",
    dependencies=ADMIN_ONLY,
)
def create_session(data: GroupSessionCreate, service: ScheduleDep) -> SessionRead:
    return SessionRead.from_model(service.create_group(data.model_dump()), service.clock.zone)


@router.patch(
    "/sessions/{session_id}", summary="Змінити групове заняття (адміністратор)", dependencies=ADMIN_ONLY
)
def update_session(session_id: int, data: GroupSessionUpdate, service: ScheduleDep) -> SessionRead:
    training = service.update_group(session_id, data.model_dump(exclude_unset=True))
    return SessionRead.from_model(training, service.clock.zone)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити заняття без записів (адміністратор)",
    dependencies=ADMIN_ONLY,
)
def delete_session(session_id: int, service: ScheduleDep) -> None:
    service.delete(session_id)


@router.post(
    "/sessions/copy-week",
    summary="Скопіювати групові заняття тижня на інший тиждень (адміністратор)",
    dependencies=ADMIN_ONLY,
)
def copy_week(data: CopyWeekIn, service: ScheduleDep) -> CopyWeekOut:
    result = service.copy_week(data.source_week, data.target_week)
    zone = service.clock.zone
    return CopyWeekOut(
        created=[SessionRead.from_model(s, zone) for s in result.created],
        skipped=[
            SkippedSession(title=s.title, start_at=s.start_at.astimezone(zone), reason=reason)
            for s, reason in result.skipped
        ],
    )


@router.get("/sessions/{session_id}/participants", summary="Хто записаний (персонал або тренер заняття)")
def session_participants(
    session_id: int, user: CurrentUser, service: ScheduleDep, db: DbSession
) -> list[ParticipantRead]:
    training = service.get(session_id)
    is_own_trainer = (
        user.role == Role.TRAINER and user.trainer is not None and user.trainer.id == training.trainer_id
    )
    if user.role not in STAFF_ROLES and not is_own_trainer:
        raise PermissionDeniedError()
    return [
        ParticipantRead(
            booking_id=b.id,
            client_id=b.client.id,
            full_name=b.client.full_name,
            phone=b.client.phone,
            status=b.status,
        )
        for b in BookingFacade(db, service.clock).session_bookings(session_id)
    ]


@router.get("/trainers/{trainer_id}/slots", summary="Вільні слоти для індивідуального заняття (публічно)")
def trainer_slots(
    trainer_id: int, service: ScheduleDep, day: Annotated[date, Query(alias="date")]
) -> list[str]:
    return [slot.isoformat() for slot in service.free_slots(trainer_id, day)]
