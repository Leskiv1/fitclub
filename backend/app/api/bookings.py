"""Booking group and individual sessions with undo (Ф-4)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import STAFF_ROLES, ClockDep, CurrentUser, DbSession, ensure_can_view_client
from app.api.errors import ERROR_RESPONSES
from app.domain.errors import BusinessRuleError, PermissionDeniedError
from app.domain.models import Role, User
from app.schemas.sessions import BookingIn, BookingRead, IndividualBookingIn, UndoOut
from app.services.bookings import BookingFacade

router = APIRouter(tags=["Записи на заняття"], responses=ERROR_RESPONSES)


def get_booking_facade(db: DbSession, clock: ClockDep) -> BookingFacade:
    return BookingFacade(db, clock)


BookingFacadeDep = Annotated[BookingFacade, Depends(get_booking_facade)]


def _client_for(user: User, client_id: int | None) -> int:
    """A client books only for themselves; staff book for the client given in the request."""
    if user.role == Role.CLIENT and user.client is not None:
        if client_id not in (None, user.client.id):
            raise PermissionDeniedError("Клієнт може записати лише себе")
        return user.client.id
    if user.role in STAFF_ROLES:
        if client_id is None:
            raise BusinessRuleError("Вкажіть клієнта, якого записуєте")
        return client_id
    raise PermissionDeniedError()


@router.post("/bookings", status_code=status.HTTP_201_CREATED, summary="Записатися на групове заняття")
def book_group(data: BookingIn, user: CurrentUser, facade: BookingFacadeDep) -> BookingRead:
    booking = facade.book(_client_for(user, data.client_id), data.session_id, user)
    return BookingRead.from_model(booking, facade.clock.zone)


@router.post(
    "/bookings/individual", status_code=status.HTTP_201_CREATED, summary="Записатися на індивідуальне заняття"
)
def book_individual(data: IndividualBookingIn, user: CurrentUser, facade: BookingFacadeDep) -> BookingRead:
    booking = facade.book_individual(_client_for(user, data.client_id), data.trainer_id, data.start_at, user)
    return BookingRead.from_model(booking, facade.clock.zone)


@router.post("/bookings/{booking_id}/cancel", summary="Скасувати запис")
def cancel_booking(booking_id: int, user: CurrentUser, facade: BookingFacadeDep) -> BookingRead:
    booking = facade.get(booking_id)
    is_own = user.role == Role.CLIENT and user.client is not None and booking.client_id == user.client.id
    if user.role not in STAFF_ROLES and not is_own:
        raise PermissionDeniedError()
    return BookingRead.from_model(facade.cancel(booking_id, user), facade.clock.zone)


@router.post("/bookings/undo", summary="Відмінити свою останню дію із записом")
def undo_last(user: CurrentUser, facade: BookingFacadeDep) -> UndoOut:
    action, booking = facade.undo_last(user)
    return UndoOut(undone=action, booking=BookingRead.from_model(booking, facade.clock.zone))


@router.get("/clients/{client_id}/bookings", summary="Записи клієнта («Мої записи»)")
def client_bookings(
    client_id: int, user: CurrentUser, facade: BookingFacadeDep, upcoming: bool = True
) -> list[BookingRead]:
    ensure_can_view_client(user, client_id)
    return [
        BookingRead.from_model(b, facade.clock.zone)
        for b in facade.client_bookings(client_id, upcoming=upcoming)
    ]
