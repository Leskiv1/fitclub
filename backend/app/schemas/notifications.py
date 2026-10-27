from datetime import datetime, time

from pydantic import Field, field_validator

from app.domain.models import (
    ClubSettings,
    Notification,
    NotificationChannel,
    NotificationKind,
    NotificationStatus,
)
from app.schemas.common import Schema


def _check_opening_hours(value: dict[str, list[str]] | None) -> dict[str, list[str]] | None:
    if value is None:
        return value
    normalized = {}
    for day, hours in value.items():
        if day not in {str(d) for d in range(7)}:
            raise ValueError("ключі — дні тижня від 0 (понеділок) до 6 (неділя)")
        if len(hours) != 2:
            raise ValueError(f'день {day}: потрібно ["HH:MM", "HH:MM"]')
        try:
            opens, closes = (datetime.strptime(h.strip(), "%H:%M").time() for h in hours)  # accepts 9:00
        except ValueError as exc:
            raise ValueError(f"день {day}: час у форматі HH:MM") from exc
        if closes <= opens:
            raise ValueError(f"день {day}: час закриття має бути пізніше за відкриття")
        normalized[day] = [f"{opens:%H:%M}", f"{closes:%H:%M}"]
    return normalized


class ClubSettingsRead(Schema):
    opening_hours: dict[str, list[str]] = Field(description='{"0": ["06:00", "23:00"], …}; 0 — понеділок')
    expiry_warning_days: int
    daily_check_time: time
    notifications_enabled: bool
    currency: str

    @classmethod
    def from_model(cls, settings: ClubSettings) -> ClubSettingsRead:
        return cls.model_validate(settings)


class ClubSettingsUpdate(Schema):
    opening_hours: dict[str, list[str]] | None = None
    expiry_warning_days: int | None = Field(None, ge=1, le=60, description="За скільки днів попереджати")
    daily_check_time: time | None = Field(None, description="Коли щодня перевіряти абонементи")
    notifications_enabled: bool | None = None
    currency: str | None = Field(None, pattern=r"^[A-Z]{3}$")

    _hours = field_validator("opening_hours")(_check_opening_hours)


class NotificationRead(Schema):
    id: int
    client_id: int
    client_name: str
    membership_id: int | None
    kind: NotificationKind
    channel: NotificationChannel
    subject: str | None
    message: str
    status: NotificationStatus
    error: str | None
    sent_at: datetime | None
    created_at: datetime

    @classmethod
    def from_model(cls, notification: Notification, zone) -> NotificationRead:
        return cls(
            id=notification.id,
            client_id=notification.client_id,
            client_name=notification.client.full_name,
            membership_id=notification.membership_id,
            kind=notification.kind,
            channel=notification.channel,
            subject=notification.subject,
            message=notification.message,
            status=notification.status,
            error=notification.error,
            sent_at=notification.sent_at.astimezone(zone) if notification.sent_at else None,
            created_at=notification.created_at.astimezone(zone),
        )


class DailyCheckOut(Schema):
    expired: int = Field(description="Скільки абонементів переведено в стан «закінчився»")
    reminders: int = Field(description="Скільки нагадувань надіслано")
    skipped: bool = Field(description="Перевірку вже виконує інший процес")
