from datetime import date, datetime

from pydantic import Field, model_validator

from app.domain.models import Booking, BookingStatus, SessionKind, TrainingSession
from app.schemas.common import Schema


class TrainerBrief(Schema):
    id: int
    full_name: str
    specialization: str


class HallBrief(Schema):
    id: int
    name: str


class SessionRead(Schema):
    id: int
    kind: SessionKind
    title: str | None
    start_at: datetime = Field(description="Час у часовому поясі клубу")
    end_at: datetime
    trainer: TrainerBrief
    hall: HallBrief
    capacity: int
    booked: int
    free_places: int

    @classmethod
    def from_model(cls, training: TrainingSession, zone) -> SessionRead:
        return cls(
            id=training.id,
            kind=training.kind,
            title=getattr(training, "title", None) or "Індивідуальне заняття",
            start_at=training.start_at.astimezone(zone),
            end_at=training.end_at.astimezone(zone),
            trainer=TrainerBrief.model_validate(training.trainer),
            hall=HallBrief.model_validate(training.hall),
            capacity=training.capacity(),
            booked=len(training.active_bookings()),
            free_places=training.free_places(),
        )


class GroupSessionCreate(Schema):
    title: str = Field(min_length=2, max_length=150)
    trainer_id: int
    hall_id: int
    start_at: datetime = Field(description="З часовим поясом, напр. 2026-11-02T18:00:00+02:00")
    end_at: datetime
    max_participants: int = Field(gt=0, le=1000)

    @model_validator(mode="after")
    def _aware(self) -> GroupSessionCreate:
        if self.start_at.tzinfo is None or self.end_at.tzinfo is None:
            raise ValueError("час має містити часовий пояс")
        return self


class GroupSessionUpdate(Schema):
    title: str | None = Field(None, min_length=2, max_length=150)
    trainer_id: int | None = None
    hall_id: int | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    max_participants: int | None = Field(None, gt=0, le=1000)


class CopyWeekIn(Schema):
    source_week: date = Field(description="Понеділок тижня, який копіюємо")
    target_week: date = Field(description="Понеділок тижня, куди копіюємо")


class SkippedSession(Schema):
    title: str
    start_at: datetime
    reason: str


class CopyWeekOut(Schema):
    created: list[SessionRead]
    skipped: list[SkippedSession]


class BookingIn(Schema):
    session_id: int
    client_id: int | None = Field(None, description="Обов'язковий для персоналу; клієнт записується сам")


class IndividualBookingIn(Schema):
    trainer_id: int
    start_at: datetime = Field(description="Початок слоту з GET /api/trainers/{id}/slots")
    client_id: int | None = None


class BookingRead(Schema):
    id: int
    status: BookingStatus
    created_at: datetime
    session: SessionRead

    @classmethod
    def from_model(cls, booking: Booking, zone) -> BookingRead:
        return cls(
            id=booking.id,
            status=booking.status,
            created_at=booking.created_at,
            session=SessionRead.from_model(booking.session, zone),
        )


class UndoOut(Schema):
    undone: str = Field(description="Яку дію відмінено: book або cancel")
    booking: BookingRead


class ParticipantRead(Schema):
    booking_id: int
    client_id: int
    full_name: str
    phone: str
    status: BookingStatus
