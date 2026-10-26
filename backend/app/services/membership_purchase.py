"""Buying a membership (Ф-5): one entry point over factories, pricing, discounts, payment and states."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.errors import BusinessRuleError, NotFoundError
from app.domain.membership.discounts import (
    DiscountContext,
    DiscountStrategy,
    LoyaltyDiscount,
    NoDiscount,
    PromoCodeDiscount,
    StudentDiscount,
)
from app.domain.membership.factories import factory_for
from app.domain.membership.pricing import PriceLine, build_price
from app.domain.models import (
    Client,
    DiscountType,
    Membership,
    MembershipOption,
    Payment,
    PaymentMethod,
    PaymentStatus,
    TariffPlan,
)
from app.repositories.clients import ClientRepository
from app.repositories.memberships import MembershipRepository, PromoCodeRepository
from app.repositories.tariffs import MembershipOptionRepository, TariffPlanRepository


@dataclass(frozen=True)
class DiscountRequest:
    type: DiscountType
    reference: str | None = None  # student card number or promo code


@dataclass(frozen=True)
class PurchaseRequest:
    client_id: int
    tariff_id: int
    option_ids: list[int] = field(default_factory=list)
    discount: DiscountRequest | None = None
    start_date: date | None = None
    payment_method: PaymentMethod = PaymentMethod.CARD


@dataclass(frozen=True)
class Quote:
    lines: list[PriceLine]
    subtotal: Decimal
    discount: DiscountStrategy
    discount_amount: Decimal
    total: Decimal
    start_date: date
    end_date: date
    visits_left: int | None


class PaymentProcessor:
    """Imitation of a payment provider: every payment succeeds immediately."""

    def charge(self, amount: Decimal, method: PaymentMethod) -> Payment:
        return Payment(amount=amount, method=method, status=PaymentStatus.PAID, paid_at=datetime.now(UTC))


class MembershipPurchaseFacade:
    """GoF: Facade — hides the subsystems used to sell a membership behind `quote()` and `purchase()`.

    Subsystems: MembershipFactory (Factory Method), PriceComponent/OptionDecorator (Decorator),
    DiscountStrategy (Strategy), PaymentProcessor, MembershipState (State) and the repositories.
    """

    def __init__(self, session: Session, payments: PaymentProcessor | None = None) -> None:
        self.session = session
        self.clients = ClientRepository(session)
        self.tariffs = TariffPlanRepository(session)
        self.options = MembershipOptionRepository(session)
        self.memberships = MembershipRepository(session)
        self.promo_codes = PromoCodeRepository(session)
        self.payments = payments or PaymentProcessor()

    def quote(self, request: PurchaseRequest, today: date | None = None) -> Quote:
        """Price and dates of a purchase without saving anything (summary step of the purchase form)."""
        return self._prepare(request, today or date.today())[3]

    def purchase(self, request: PurchaseRequest, today: date | None = None) -> Membership:
        client, tariff, options, quote = self._prepare(request, today or date.today())

        membership = factory_for(tariff.type).issue(client, tariff, quote.start_date, options)
        membership.total_price = quote.total
        membership.discount_type = quote.discount.type
        membership.discount_reference = quote.discount.reference
        membership.discount_amount = quote.discount_amount
        membership.payment = self.payments.charge(quote.total, request.payment_method)
        membership.activate()  # Pending → Active once paid

        self.memberships.add(membership)
        self.session.commit()
        return membership

    # --- steps hidden behind the facade ---

    def _prepare(
        self, request: PurchaseRequest, today: date
    ) -> tuple[Client, TariffPlan, list[MembershipOption], Quote]:
        client, tariff, options = self._load(request)
        start = self._start_date(client, request.start_date, today)
        terms = factory_for(tariff.type).create_membership(tariff, start)  # transient, never added

        price = build_price(tariff, options)
        subtotal = price.price()
        strategy = self._discount_strategy(request.discount)
        context = DiscountContext(
            client=client,
            amount=subtotal,
            today=today,
            paid_memberships=self.memberships.count_paid(client.id),
        )
        discount = strategy.discount(context)
        quote = Quote(
            lines=price.lines(),
            subtotal=subtotal,
            discount=strategy,
            discount_amount=discount,
            total=subtotal - discount,
            start_date=terms.start_date,
            end_date=terms.end_date,
            visits_left=terms.visits_left,
        )
        return client, tariff, options, quote

    def _load(self, request: PurchaseRequest) -> tuple[Client, TariffPlan, list[MembershipOption]]:
        client = self.clients.get(request.client_id)
        if client is None:
            raise NotFoundError("Клієнт", request.client_id)
        tariff = self.tariffs.get(request.tariff_id)
        if tariff is None:
            raise NotFoundError("Тариф", request.tariff_id)
        if not tariff.is_active:
            raise BusinessRuleError(f"Тариф «{tariff.name}» більше не продається")

        options = []
        for option_id in dict.fromkeys(request.option_ids):  # ignore duplicates, keep order
            option = self.options.get(option_id)
            if option is None:
                raise NotFoundError("Опція", option_id)
            if not option.is_active:
                raise BusinessRuleError(f"Опція «{option.name}» недоступна")
            options.append(option)
        return client, tariff, options

    def _start_date(self, client: Client, requested: date | None, today: date) -> date:
        """A purchase during a running membership continues it from the next day (renewal)."""
        if requested is not None and requested < today:
            raise BusinessRuleError("Дата початку не може бути в минулому")
        start = requested or today
        running = self.memberships.latest_running(client.id, start)
        if running is not None:
            start = max(start, running.end_date + timedelta(days=1))
        return start

    def _discount_strategy(self, discount: DiscountRequest | None) -> DiscountStrategy:
        if discount is None:
            return NoDiscount()
        match discount.type:
            case DiscountType.STUDENT:
                return StudentDiscount(discount.reference)
            case DiscountType.LOYALTY:
                return LoyaltyDiscount()
            case DiscountType.PROMO:
                code = (discount.reference or "").strip().upper()
                return PromoCodeDiscount(self.promo_codes.get_by_code(code), code)
