"""Discounts on a membership purchase; exactly one discount strategy is applied per purchase."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.domain.errors import BusinessRuleError
from app.domain.models import Client, DiscountType, PromoCode

CENT = Decimal("0.01")
STUDENT_MAX_AGE_EXCLUSIVE = 21
STUDENT_CARD_RE = re.compile(r"^[A-ZА-ЯІЇЄҐ]{2}\d{8}$")
LOYALTY_MIN_PAID_MEMBERSHIPS = 12


@dataclass(frozen=True)
class DiscountContext:
    """Everything a strategy may need; prepared by the purchase facade so strategies stay free of the DB."""

    client: Client
    amount: Decimal
    today: date
    paid_memberships: int = 0


class DiscountStrategy(ABC):
    """GoF: Strategy — Strategy: checks whether the discount applies and computes its amount."""

    type: DiscountType | None = None
    percent: int = 0
    reference: str | None = None

    def discount(self, context: DiscountContext) -> Decimal:
        self._check(context)
        return (context.amount * self.percent / 100).quantize(CENT, rounding=ROUND_HALF_UP)

    @abstractmethod
    def _check(self, context: DiscountContext) -> None:
        """Raise BusinessRuleError if the client is not entitled to this discount."""


class NoDiscount(DiscountStrategy):
    """GoF: Strategy — ConcreteStrategy: full price."""

    def _check(self, context: DiscountContext) -> None:
        return None


class StudentDiscount(DiscountStrategy):
    """GoF: Strategy — ConcreteStrategy: 10% for students younger than 21 with a student card number."""

    type = DiscountType.STUDENT
    percent = 10

    def __init__(self, student_card: str | None) -> None:
        self.reference = (student_card or "").strip().upper().replace(" ", "")

    def _check(self, context: DiscountContext) -> None:
        if not STUDENT_CARD_RE.fullmatch(self.reference):
            raise BusinessRuleError("Вкажіть номер студентського квитка у форматі КВ12345678")
        if context.client.age(context.today) >= STUDENT_MAX_AGE_EXCLUSIVE:
            raise BusinessRuleError(
                f"Студентська знижка діє для клієнтів до {STUDENT_MAX_AGE_EXCLUSIVE} років"
            )


class LoyaltyDiscount(DiscountStrategy):
    """GoF: Strategy — ConcreteStrategy: 15% for regular clients (a year of paid memberships)."""

    type = DiscountType.LOYALTY
    percent = 15

    def _check(self, context: DiscountContext) -> None:
        if context.paid_memberships < LOYALTY_MIN_PAID_MEMBERSHIPS:
            raise BusinessRuleError(
                f"Знижка постійного клієнта діє після {LOYALTY_MIN_PAID_MEMBERSHIPS} оплачених абонементів "
                f"(зараз — {context.paid_memberships})"
            )


class PromoCodeDiscount(DiscountStrategy):
    """GoF: Strategy — ConcreteStrategy: the percentage of an active promo code."""

    type = DiscountType.PROMO

    def __init__(self, promo: PromoCode | None, code: str) -> None:
        self.promo = promo
        self.reference = code
        self.percent = promo.percent if promo else 0

    def _check(self, context: DiscountContext) -> None:
        if self.promo is None or not self.promo.is_usable(context.today):
            raise BusinessRuleError(f"Промокод «{self.reference}» недійсний або прострочений")
