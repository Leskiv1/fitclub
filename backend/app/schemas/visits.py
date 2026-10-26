from datetime import date, datetime

from pydantic import Field

from app.domain.models import MembershipStatus, Visit
from app.schemas.common import Schema


class CheckInIn(Schema):
    client_id: int


class VisitRead(Schema):
    id: int
    checked_in_at: datetime = Field(description="Час входу в часовому поясі клубу")
    visit_date: date
    membership_id: int
    tariff_name: str
    membership_status: MembershipStatus
    visits_left: int | None = Field(description="Залишок відвідувань після цього входу; NULL — безліміт")

    @classmethod
    def from_model(cls, visit: Visit, zone) -> VisitRead:
        membership = visit.membership
        return cls(
            id=visit.id,
            checked_in_at=visit.checked_in_at.astimezone(zone),
            visit_date=visit.visit_date,
            membership_id=membership.id,
            tariff_name=membership.tariff_plan.name,
            membership_status=membership.status,
            visits_left=membership.visits_left,
        )


class TodayVisitRead(VisitRead):
    client_id: int
    client_name: str
    client_phone: str

    @classmethod
    def from_model(cls, visit: Visit, zone) -> TodayVisitRead:
        client = visit.membership.client
        base = VisitRead.from_model(visit, zone).model_dump()
        return cls(**base, client_id=client.id, client_name=client.full_name, client_phone=client.phone)
