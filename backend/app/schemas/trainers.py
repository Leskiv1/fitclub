from datetime import time

from pydantic import EmailStr, Field, model_validator

from app.domain.models import Trainer
from app.schemas.common import Name, Password, Schema


class WorkShiftSchema(Schema):
    weekday: int = Field(ge=0, le=6, description="0 — понеділок, 6 — неділя")
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def _check_order(self) -> WorkShiftSchema:
        if self.end_time <= self.start_time:
            raise ValueError("кінець зміни має бути пізніше за початок")
        return self


def _check_shift_overlaps(shifts: list[WorkShiftSchema] | None) -> None:
    for i, a in enumerate(shifts or []):
        for b in (shifts or [])[i + 1 :]:
            if a.weekday == b.weekday and a.start_time < b.end_time and b.start_time < a.end_time:
                raise ValueError("зміни тренера в один день не можуть перетинатися")


class TrainerCreate(Schema):
    full_name: Name
    specialization: str = Field(min_length=2, max_length=150)
    bio: str | None = None
    photo_url: str | None = Field(None, max_length=500)
    email: EmailStr
    password: Password
    work_shifts: list[WorkShiftSchema] = []

    @model_validator(mode="after")
    def _check_shifts(self) -> TrainerCreate:
        _check_shift_overlaps(self.work_shifts)
        return self


class TrainerUpdate(Schema):
    """PATCH; if `work_shifts` is sent, it replaces the whole schedule."""

    full_name: Name | None = None
    specialization: str | None = Field(None, min_length=2, max_length=150)
    bio: str | None = None
    photo_url: str | None = Field(None, max_length=500)
    email: EmailStr | None = None
    work_shifts: list[WorkShiftSchema] | None = None

    @model_validator(mode="after")
    def _check_shifts(self) -> TrainerUpdate:
        _check_shift_overlaps(self.work_shifts)
        return self


class TrainerRead(Schema):
    id: int
    full_name: str
    specialization: str
    bio: str | None
    photo_url: str | None
    email: str
    work_shifts: list[WorkShiftSchema]

    @classmethod
    def from_model(cls, trainer: Trainer) -> TrainerRead:
        return cls(
            id=trainer.id,
            full_name=trainer.full_name,
            specialization=trainer.specialization,
            bio=trainer.bio,
            photo_url=trainer.photo_url,
            email=trainer.user.email,
            work_shifts=[WorkShiftSchema.model_validate(shift) for shift in trainer.work_shifts],
        )
