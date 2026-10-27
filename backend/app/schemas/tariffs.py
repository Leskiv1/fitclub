from decimal import Decimal

from pydantic import Field

from app.domain.models import TariffType
from app.schemas.common import Schema


class TariffPlanCreate(Schema):
    name: str = Field(min_length=2, max_length=100)
    type: TariffType
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    duration_days: int = Field(gt=0, le=366 * 3)
    visit_limit: int | None = Field(None, gt=0, description="NULL — безліміт")
    description: str | None = None
    is_active: bool = True


class TariffPlanUpdate(Schema):
    name: str | None = Field(None, min_length=2, max_length=100)
    type: TariffType | None = None
    price: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=2)
    duration_days: int | None = Field(None, gt=0, le=366 * 3)
    visit_limit: int | None = Field(None, gt=0)
    description: str | None = None
    is_active: bool | None = None


class TariffPlanRead(Schema):
    id: int
    name: str
    type: TariffType
    price: Decimal
    duration_days: int
    visit_limit: int | None
    description: str | None
    is_active: bool


class MembershipOptionCreate(Schema):
    name: str = Field(min_length=2, max_length=100)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    is_active: bool = True


class MembershipOptionUpdate(Schema):
    name: str | None = Field(None, min_length=2, max_length=100)
    price: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=2)
    is_active: bool | None = None


class MembershipOptionRead(Schema):
    id: int
    name: str
    price: Decimal
    is_active: bool
