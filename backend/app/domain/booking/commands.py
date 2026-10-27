"""Booking actions as objects that can be executed, stored in history and undone."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import Booking, BookingActionType, BookingStatus, Client, TrainingSession


class BookingCommand(ABC):
    """GoF: Command — Command. Encapsulates one action on a booking together with its reversal."""

    action: BookingActionType

    @property
    @abstractmethod
    def booking(self) -> Booking: ...

    @abstractmethod
    def execute(self) -> Booking: ...

    @abstractmethod
    def undo(self) -> Booking: ...


class BookSessionCommand(BookingCommand):
    """GoF: Command — ConcreteCommand: books a client for a session; undo cancels that booking."""

    action = BookingActionType.BOOK

    def __init__(self, session: TrainingSession | None = None, client: Client | None = None) -> None:
        self.session = session
        self.client = client
        self._booking: Booking | None = None

    @classmethod
    def for_booking(cls, booking: Booking) -> BookSessionCommand:
        """Rebuilds an executed command from history (HTTP requests share no memory)."""
        command = cls()
        command._booking = booking
        return command

    @property
    def booking(self) -> Booking:
        return self._booking

    def execute(self) -> Booking:
        self._booking = Booking(session=self.session, client=self.client, status=BookingStatus.BOOKED)
        return self._booking

    def undo(self) -> Booking:
        self._booking.cancel()
        return self._booking


class CancelBookingCommand(BookingCommand):
    """GoF: Command — ConcreteCommand: cancels a booking; undo restores it."""

    action = BookingActionType.CANCEL

    def __init__(self, booking: Booking) -> None:
        self._booking = booking

    @classmethod
    def for_booking(cls, booking: Booking) -> CancelBookingCommand:
        return cls(booking)

    @property
    def booking(self) -> Booking:
        return self._booking

    def execute(self) -> Booking:
        self._booking.cancel()
        return self._booking

    def undo(self) -> Booking:
        self._booking.restore()
        return self._booking


COMMANDS: dict[BookingActionType, type[BookSessionCommand] | type[CancelBookingCommand]] = {
    BookingActionType.BOOK: BookSessionCommand,
    BookingActionType.CANCEL: CancelBookingCommand,
}
