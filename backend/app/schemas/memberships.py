from datetime import date, datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.domain.models import DiscountType, Membership, MembershipStatus, PaymentMethod, TariffType
from app.schemas.common import Schema
from app.services.membership_purchase import Quote


class DiscountIn(Schema):
    type: DiscountType
    reference: str | None = Field(
        None, max_length=50, description="Номер студентського квитка (student) або промокод (promo)"
    )


class QuoteIn(Schema):
    client_id: int | None = Field(None, description="Обов'язковий для персоналу; клієнт купує для себе")
    tariff_id: int
    option_ids: list[int] = []
    discount: DiscountIn | None = None
    start_date: date | None = Field(
        None, description="За замовчуванням — сьогодні або після поточного абонемента"
    )


class PurchaseIn(QuoteIn):
    payment_method: PaymentMethod = PaymentMethod.ONLINE


class PriceLineOut(Schema):
    name: str
    amount: Decimal


class DiscountOut(Schema):
    type: DiscountType
    percent: int
    reference: str | None
    amount: Decimal


class QuoteOut(Schema):
    lines: list[PriceLineOut]
    subtotal: Decimal
    discount: DiscountOut | None
    total: Decimal
    start_date: date
    end_date: date
    visits_left: int | None

    @classmethod
    def from_quote(cls, quote: Quote) -> QuoteOut:
        discount = None
        if quote.discount.type is not None:
            discount = DiscountOut(
                type=quote.discount.type,
                percent=quote.discount.percent,
                reference=quote.discount.reference,
                amount=quote.discount_amount,
            )
        return cls(
            lines=[PriceLineOut(name=line.name, amount=line.amount) for line in quote.lines],
            subtotal=quote.subtotal,
            discount=discount,
            total=quote.total,
            start_date=quote.start_date,
            end_date=quote.end_date,
            visits_left=quote.visits_left,
        )


class TariffBrief(Schema):
    id: int
    name: str
    type: TariffType


class OptionBrief(Schema):
    id: int
    name: str
    price: Decimal


class PaymentOut(Schema):
    amount: Decimal
    method: PaymentMethod
    paid_at: datetime


class MembershipRead(Schema):
    id: int
    client_id: int
    tariff: TariffBrief
    status: MembershipStatus
    start_date: date
    end_date: date
    days_left: int
    visits_left: int | None
    frozen_at: date | None
    frozen_days: int
    options: list[OptionBrief]
    total_price: Decimal
    discount_type: DiscountType | None
    discount_amount: Decimal
    payment: PaymentOut | None
    created_at: datetime

    @classmethod
    def from_model(cls, membership: Membership) -> MembershipRead:
        return cls(
            id=membership.id,
            client_id=membership.client_id,
            tariff=TariffBrief.model_validate(membership.tariff_plan),
            status=membership.status,
            start_date=membership.start_date,
            end_date=membership.end_date,
            days_left=membership.days_left(),
            visits_left=membership.visits_left,
            frozen_at=membership.frozen_at,
            frozen_days=membership.frozen_days,
            options=[OptionBrief.model_validate(option) for option in membership.options],
            total_price=membership.total_price,
            discount_type=membership.discount_type,
            discount_amount=membership.discount_amount,
            payment=PaymentOut.model_validate(membership.payment) if membership.payment else None,
            created_at=membership.created_at,
        )


def _normalize_code(value: str) -> str:
    return value.strip().upper()


class PromoCodeCreate(Schema):
    code: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")
    percent: int = Field(ge=1, le=90)
    valid_until: date | None = None
    is_active: bool = True

    _code = field_validator("code")(_normalize_code)


class PromoCodeUpdate(Schema):
    code: str | None = Field(None, min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")
    percent: int | None = Field(None, ge=1, le=90)
    valid_until: date | None = None
    is_active: bool | None = None

    @field_validator("code")
    @classmethod
    def _code(cls, value: str | None) -> str | None:
        return _normalize_code(value) if value else value


class PromoCodeRead(Schema):
    id: int
    code: str
    percent: int
    valid_until: date | None
    is_active: bool
