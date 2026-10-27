from datetime import date, datetime

from pydantic import EmailStr, Field, field_validator

from app.domain.models import Client, MembershipStatus, NotificationChannel
from app.schemas.common import Name, Password, Phone, Schema


def _check_birth_date(value: date | None) -> date | None:
    if value is not None and not date(1900, 1, 1) <= value <= date.today():
        raise ValueError("дата народження має бути в минулому")
    return value


class ClientCreate(Schema):
    full_name: Name
    birth_date: date
    phone: Phone
    email: EmailStr
    password: Password
    notification_channel: NotificationChannel = NotificationChannel.EMAIL

    _birth_date = field_validator("birth_date")(_check_birth_date)


class ClientUpdate(Schema):
    """PATCH: only the fields that were sent are changed."""

    full_name: Name | None = None
    birth_date: date | None = None
    phone: Phone | None = None
    email: EmailStr | None = None
    notification_channel: NotificationChannel | None = None

    _birth_date = field_validator("birth_date")(_check_birth_date)


class MembershipBrief(Schema):
    """Current (or latest) membership shown in the client registry."""

    id: int
    tariff_name: str
    status: MembershipStatus
    start_date: date
    end_date: date
    visits_left: int | None = Field(description="NULL — безліміт")


class ClientRead(Schema):
    id: int
    full_name: str
    birth_date: date
    age: int
    phone: str
    email: str
    notification_channel: NotificationChannel
    created_at: datetime
    membership: MembershipBrief | None

    @classmethod
    def from_model(cls, client: Client) -> ClientRead:
        membership = client.active_membership() or (client.memberships[-1] if client.memberships else None)
        brief = None
        if membership is not None:
            brief = MembershipBrief(
                id=membership.id,
                tariff_name=membership.tariff_plan.name,
                status=membership.status,
                start_date=membership.start_date,
                end_date=membership.end_date,
                visits_left=membership.visits_left,
            )
        return cls(
            id=client.id,
            full_name=client.full_name,
            birth_date=client.birth_date,
            age=client.age(),
            phone=client.phone,
            email=client.user.email,
            notification_channel=client.notification_channel,
            created_at=client.created_at,
            membership=brief,
        )


class ClientShort(Schema):
    id: int
    full_name: str
    phone: str
