"""Booking group and individual sessions (Ф-4): checks, commands with undo and history."""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.domain.booking.chain import BookingContext, BookingDeniedError, build_booking_chain
from app.domain.booking.commands import COMMANDS, BookingCommand, BookSessionCommand, CancelBookingCommand
from app.domain.errors import BusinessRuleError, NotFoundError
from app.domain.models import (
    Booking,
    BookingAction,
    BookingActionType,
    BookingStatus,
    Client,
    IndividualSession,
    Trainer,
    TrainingSession,
    User,
)
from app.repositories.clients import ClientRepository
from app.repositories.training_sessions import (
    BookingActionRepository,
    BookingRepository,
    TrainingSessionRepository,
)
from app.services.schedule import SLOT


class BookingInvoker:
    """GoF: Command — Invoker. Executes commands, keeps their history and undoes the latest one."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, command: BookingCommand, actor: User) -> Booking:
        booking = command.execute()
        self.session.add(booking)
        self.session.add(BookingAction(booking=booking, action=command.action, actor_user_id=actor.id))
        return booking

    def undo(self, action: BookingAction, now: datetime) -> Booking:
        command = COMMANDS[action.action].for_booking(action.booking)  # rebuilt from history
        booking = command.undo()
        action.undone_at = now
        return booking


class BookingFacade:
    """GoF: Facade — booking, cancelling and undoing in one call each.

    Subsystems: repositories with row locks, the Chain of Responsibility of booking checks,
    booking commands and their invoker.
    """

    def __init__(self, session: Session, clock: Clock | None = None) -> None:
        self.session = session
        self.clock = clock or Clock()
        self.clients = ClientRepository(session)
        self.sessions = TrainingSessionRepository(session)
        self.bookings = BookingRepository(session)
        self.actions = BookingActionRepository(session)
        self.invoker = BookingInvoker(session)
        self.chain = build_booking_chain()

    def book(self, client_id: int, session_id: int, actor: User) -> Booking:
        client = self._client(client_id)
        # locked until commit: two clients cannot take the last place at the same moment
        training = self.sessions.get_for_update(session_id)
        if training is None or training.is_cancelled:
            raise NotFoundError("Заняття", session_id)
        self.chain.handle(self._context(client, training))
        booking = self.invoker.execute(BookSessionCommand(training, client), actor)
        self._flush_or_deny("already_booked", "Клієнт уже записаний на це заняття")
        self.session.commit()
        return booking

    def book_individual(self, client_id: int, trainer_id: int, start: datetime, actor: User) -> Booking:
        client = self._client(client_id)
        # the trainer row is locked so two clients cannot take the same slot; the DB exclusion
        # constraint is the second line of defence
        trainer = self.session.scalar(select(Trainer).where(Trainer.id == trainer_id).with_for_update())
        if trainer is None:
            raise NotFoundError("Тренер", trainer_id)

        start = start.astimezone(self.clock.zone)
        end = start + SLOT
        if start.minute or start.second or start.microsecond:
            raise BusinessRuleError("Індивідуальні заняття починаються на початку години")
        if not any(shift.covers(start) and shift.covers(end) for shift in trainer.work_shifts):
            raise BookingDeniedError("trainer_off_shift", f"{trainer.full_name} не працює в цей час")
        if self.sessions.conflicts(start, end, trainer_id=trainer.id):
            raise BookingDeniedError("slot_taken", "Цей час у тренера вже зайнятий")
        hall = self.sessions.first_free_hall(start, end)
        if hall is None:
            raise BookingDeniedError("no_free_hall", "У цей час немає вільного залу")

        # checks run without autoflush: the new session must not reach the DB before they pass
        with self.session.no_autoflush:
            training = IndividualSession(trainer=trainer, hall=hall, start_at=start, end_at=end)
            self.chain.handle(self._context(client, training))
        self.session.add(training)
        booking = self.invoker.execute(BookSessionCommand(training, client), actor)
        self._flush_or_deny("slot_taken", "Цей час у тренера вже зайнятий")
        self.session.commit()
        return booking

    def cancel(self, booking_id: int, actor: User) -> Booking:
        booking = self.get(booking_id)
        if booking.status == BookingStatus.CANCELLED:
            raise BusinessRuleError("Запис уже скасовано")
        if booking.session.start_at <= self.clock.now():
            raise BookingDeniedError("session_started", "Скасувати можна лише до початку заняття")
        self.invoker.execute(CancelBookingCommand(booking), actor)
        self.session.flush()
        self.session.commit()
        return booking

    def undo_last(self, actor: User) -> tuple[BookingActionType, Booking]:
        action = self.actions.last_not_undone(actor.id)
        if action is None:
            raise BusinessRuleError("Немає дій, які можна відмінити")
        booking = action.booking
        training = self.sessions.get_for_update(booking.session_id)
        if training.start_at <= self.clock.now():
            raise BookingDeniedError("session_started", "Заняття вже почалося — дію відмінити не можна")

        if action.action == BookingActionType.BOOK:
            if booking.status == BookingStatus.CANCELLED:
                raise BusinessRuleError("Запис уже скасовано іншою дією")
        else:
            # undoing a cancellation re-books: the place may have been taken in the meantime
            self.chain.handle(self._context(booking.client, training))
        self.invoker.undo(action, self.clock.now())
        self._flush_or_deny("slot_taken", "Цей час у тренера вже зайнятий")
        self.session.commit()
        return action.action, booking

    def get(self, booking_id: int) -> Booking:
        booking = self.bookings.get(booking_id)
        if booking is None:
            raise NotFoundError("Запис", booking_id)
        return booking

    def client_bookings(self, client_id: int, *, upcoming: bool) -> Sequence[Booking]:
        self._client(client_id)
        return self.bookings.for_client(client_id, since=self.clock.now() if upcoming else None)

    def session_bookings(self, session_id: int) -> Sequence[Booking]:
        return self.bookings.for_session(session_id)

    # --- steps ---

    def _client(self, client_id: int) -> Client:
        client = self.clients.get(client_id)
        if client is None:
            raise NotFoundError("Клієнт", client_id)
        return client

    def _context(self, client: Client, training: TrainingSession) -> BookingContext:
        active = self.bookings.active_for(client.id, training.id) if training.id else None
        return BookingContext(
            client=client,
            session=training,
            now=self.clock.now(),
            session_day=training.start_at.astimezone(self.clock.zone).date(),
            active_booking=active,
        )

    def _flush_or_deny(self, code: str, message: str) -> None:
        try:
            self.session.flush()
        except IntegrityError as exc:  # exclusion constraint or unique active booking index
            self.session.rollback()
            raise BookingDeniedError(code, message) from exc
