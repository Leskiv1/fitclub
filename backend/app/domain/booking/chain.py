"""Checks performed before a client is booked for a training session (Ф-4)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime

from app.domain.errors import BusinessRuleError
from app.domain.models import Booking, Client, TrainingSession


class BookingDeniedError(BusinessRuleError):
    """Booking refused; `code` tells why."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class BookingContext:
    client: Client
    session: TrainingSession
    now: datetime
    session_day: date  # local date of the session
    active_booking: Booking | None  # an existing non-cancelled booking of this client for the session


class BookingHandler(ABC):
    """GoF: Chain of Responsibility — Handler."""

    def __init__(self) -> None:
        self._next: BookingHandler | None = None

    def set_next(self, handler: BookingHandler) -> BookingHandler:
        self._next = handler
        return handler

    def handle(self, context: BookingContext) -> None:
        self.check(context)
        if self._next is not None:
            self._next.handle(context)

    @abstractmethod
    def check(self, context: BookingContext) -> None: ...


class SessionInFutureHandler(BookingHandler):
    """GoF: Chain of Responsibility — ConcreteHandler."""

    def check(self, context: BookingContext) -> None:
        if context.session.start_at <= context.now:
            raise BookingDeniedError("session_started", "Заняття вже почалося або минуло")


class HasValidMembershipHandler(BookingHandler):
    """GoF: Chain of Responsibility — ConcreteHandler. Active, not frozen, with visits left on that day."""

    def check(self, context: BookingContext) -> None:
        if not any(m.is_valid(context.session_day) for m in context.client.memberships):
            raise BookingDeniedError(
                "no_valid_membership",
                f"Немає активного абонемента, що діє {context.session_day:%d.%m.%Y}",
            )


class NotAlreadyBookedHandler(BookingHandler):
    """GoF: Chain of Responsibility — ConcreteHandler."""

    def check(self, context: BookingContext) -> None:
        if context.active_booking is not None:
            raise BookingDeniedError("already_booked", "Клієнт уже записаний на це заняття")


class HasFreePlaceHandler(BookingHandler):
    """GoF: Chain of Responsibility — ConcreteHandler."""

    def check(self, context: BookingContext) -> None:
        if context.session.is_full():
            raise BookingDeniedError("no_free_places", "На заняття не лишилось вільних місць")


def build_booking_chain() -> BookingHandler:
    head = SessionInFutureHandler()
    head.set_next(HasValidMembershipHandler()).set_next(NotAlreadyBookedHandler()).set_next(
        HasFreePlaceHandler()
    )
    return head
