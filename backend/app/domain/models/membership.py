from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Numeric, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.models.enums import MembershipStatus, PaymentMethod, PaymentStatus, str_enum

if TYPE_CHECKING:
    from app.domain.models.client import Client
    from app.domain.models.tariff import MembershipOption, TariffPlan
    from app.domain.models.visit import Visit

membership_option_links = Table(
    "membership_option_links",
    Base.metadata,
    Column("membership_id", ForeignKey("memberships.id", ondelete="CASCADE"), primary_key=True),
    Column("option_id", ForeignKey("membership_options.id", ondelete="RESTRICT"), primary_key=True),
)


class Membership(Base):
    """Membership bought by a client according to a tariff plan."""

    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="date_order"),
        CheckConstraint("visits_left IS NULL OR visits_left >= 0", name="visits_left_non_negative"),
        CheckConstraint("total_price >= 0", name="total_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    tariff_plan_id: Mapped[int] = mapped_column(ForeignKey("tariff_plans.id", ondelete="RESTRICT"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date, index=True)
    visits_left: Mapped[int | None] = mapped_column(comment="NULL means unlimited visits")
    status: Mapped[MembershipStatus] = mapped_column(
        str_enum(MembershipStatus), default=MembershipStatus.PENDING
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped[Client] = relationship(back_populates="memberships")
    tariff_plan: Mapped[TariffPlan] = relationship(back_populates="memberships")
    options: Mapped[list[MembershipOption]] = relationship(secondary=membership_option_links)
    payment: Mapped[Payment | None] = relationship(back_populates="membership")
    visits: Mapped[list[Visit]] = relationship(back_populates="membership", order_by="Visit.checked_in_at")

    def is_valid(self, on: date | None = None) -> bool:
        """Active, within its dates and with visits left."""
        on = on or date.today()
        in_dates = self.start_date <= on <= self.end_date
        has_visits = self.visits_left is None or self.visits_left > 0
        return self.status == MembershipStatus.ACTIVE and in_dates and has_visits

    def days_left(self, today: date | None = None) -> int:
        today = today or date.today()
        return max(0, (self.end_date - today).days)


class Payment(Base):
    """Payment for a membership; one membership is paid once."""

    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount >= 0", name="amount_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    membership_id: Mapped[int] = mapped_column(ForeignKey("memberships.id", ondelete="CASCADE"), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    method: Mapped[PaymentMethod] = mapped_column(str_enum(PaymentMethod))
    status: Mapped[PaymentStatus] = mapped_column(str_enum(PaymentStatus), default=PaymentStatus.PAID)

    membership: Mapped[Membership] = relationship(back_populates="payment")
