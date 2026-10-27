"""Schedule of group sessions (Ф-4) and free slots of trainers for individual sessions."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.domain.errors import BusinessRuleError, ConflictError, NotFoundError
from app.domain.models import GroupSession, Hall, SessionKind, Trainer, TrainingSession
from app.repositories.halls import HallRepository
from app.repositories.trainers import TrainerRepository
from app.repositories.training_sessions import TrainingSessionRepository

SLOT = timedelta(hours=1)


@dataclass
class CopyWeekResult:
    created: list[GroupSession] = field(default_factory=list)
    skipped: list[tuple[GroupSession, str]] = field(default_factory=list)


class ScheduleService:
    def __init__(self, session: Session, clock: Clock | None = None) -> None:
        self.session = session
        self.clock = clock or Clock()
        self.sessions = TrainingSessionRepository(session)
        self.trainers = TrainerRepository(session)
        self.halls = HallRepository(session)

    # --- reading ---

    def week(
        self, start: date, *, kind: SessionKind | None = None, trainer_id: int | None = None
    ) -> Sequence[TrainingSession]:
        begin = datetime.combine(start, time.min, tzinfo=self.clock.zone)
        return self.sessions.in_period(begin, begin + timedelta(days=7), kind=kind, trainer_id=trainer_id)

    def get(self, session_id: int) -> TrainingSession:
        training = self.sessions.get(session_id)
        if training is None or training.is_cancelled:
            raise NotFoundError("Заняття", session_id)
        return training

    def free_slots(self, trainer_id: int, day: date) -> list[datetime]:
        """Future hourly slots inside the trainer's shifts when both the trainer and some hall are free."""
        trainer = self._trainer(trainer_id)
        now = self.clock.now()
        slots = []
        for shift in trainer.work_shifts:
            if shift.weekday != day.weekday():
                continue
            start = datetime.combine(day, shift.start_time, tzinfo=self.clock.zone)
            if start.minute or start.second:  # slots start on the hour
                start = start.replace(minute=0, second=0) + SLOT
            while start + SLOT <= datetime.combine(day, shift.end_time, tzinfo=self.clock.zone):
                end = start + SLOT
                busy = self.sessions.conflicts(start, end, trainer_id=trainer.id)
                if start > now and not busy and self.sessions.first_free_hall(start, end) is not None:
                    slots.append(start)
                start = end
        return sorted(slots)

    # --- administrator: group sessions ---

    def create_group(self, values: dict[str, Any]) -> GroupSession:
        training = GroupSession(**values)
        self._validate(training)
        return self._save(training)

    def update_group(self, session_id: int, changes: dict[str, Any]) -> GroupSession:
        training = self.get(session_id)
        if not isinstance(training, GroupSession):
            raise BusinessRuleError("Індивідуальні заняття змінює лише запис клієнта")
        booked = len(training.active_bookings())
        for name, value in changes.items():
            setattr(training, name, value)
        if training.max_participants < booked:
            raise BusinessRuleError(f"На заняття вже записано {booked} осіб — менше місць зробити не можна")
        self._validate(training, exclude_id=training.id)
        return self._save(training)

    def delete(self, session_id: int) -> None:
        training = self.get(session_id)
        if training.active_bookings():
            raise ConflictError("На заняття є записи — спершу скасуйте їх")
        self.session.delete(training)
        self.session.commit()

    def copy_week(self, source_monday: date, target_monday: date) -> CopyWeekResult:
        """GoF: Prototype — every group session of the source week clones itself into the target week."""
        if source_monday.weekday() != 0 or target_monday.weekday() != 0:
            raise BusinessRuleError("Тижні задаються датою понеділка")
        current_monday = self.clock.today() - timedelta(days=self.clock.today().weekday())
        if target_monday < current_monday:
            raise BusinessRuleError("Копіювати можна лише в поточний або майбутній тиждень")

        days = (target_monday - source_monday).days
        result = CopyWeekResult()
        for original in self.week(source_monday, kind=SessionKind.GROUP):
            copy = original.clone(days, self.clock.zone)
            try:
                self._validate(copy)
                with self.session.begin_nested():  # a conflict skips one session, not the whole copy
                    self.session.add(copy)
                    self.session.flush()
            except (ConflictError, BusinessRuleError) as exc:
                result.skipped.append((copy, exc.message))
                continue
            except IntegrityError:
                result.skipped.append((copy, "Тренер або зал уже зайняті в цей час"))
                continue
            result.created.append(copy)
        self.session.commit()
        return result

    # --- steps ---

    def _trainer(self, trainer_id: int) -> Trainer:
        trainer = self.trainers.get(trainer_id)
        if trainer is None:
            raise NotFoundError("Тренер", trainer_id)
        return trainer

    def _hall(self, hall_id: int) -> Hall:
        hall = self.halls.get(hall_id)
        if hall is None:
            raise NotFoundError("Зал", hall_id)
        return hall

    def _validate(self, training: TrainingSession, exclude_id: int | None = None) -> None:
        if training.end_at <= training.start_at:
            raise BusinessRuleError("Заняття має закінчуватися пізніше, ніж починається")
        if training.start_at <= self.clock.now():
            raise BusinessRuleError("Заняття можна планувати лише на майбутнє")
        trainer = self._trainer(training.trainer_id)
        hall = self._hall(training.hall_id)
        if isinstance(training, GroupSession) and training.max_participants > hall.capacity:
            raise BusinessRuleError(f"Зал «{hall.name}» вміщує лише {hall.capacity} осіб")

        start, end = (moment.astimezone(self.clock.zone) for moment in (training.start_at, training.end_at))
        if not any(shift.covers(start) and shift.covers(end) for shift in trainer.work_shifts):
            raise BusinessRuleError(f"{trainer.full_name} не працює в цей час")
        for other in self.sessions.conflicts(
            training.start_at, training.end_at, trainer_id=trainer.id, hall_id=hall.id, exclude_id=exclude_id
        ):
            who = f"Тренер {trainer.full_name}" if other.trainer_id == trainer.id else f"Зал «{hall.name}»"
            raise ConflictError(f"{who} уже зайнятий о {other.start_at.astimezone(self.clock.zone):%H:%M}")

    def _save(self, training: GroupSession) -> GroupSession:
        self.session.add(training)
        try:
            self.session.flush()
        except IntegrityError as exc:  # exclusion constraint: a concurrent request took the time first
            self.session.rollback()
            raise ConflictError("Тренер або зал уже зайняті в цей час") from exc
        self.session.commit()
        return training
