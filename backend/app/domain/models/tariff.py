from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.models.enums import TariffType, str_enum

if TYPE_CHECKING:
    from app.domain.models.membership import Membership


class TariffPlan(Base):
    """Tariff plan (Ф-5): defines price, duration and the visit limit of a membership."""

    __tablename__ = "tariff_plans"
    __table_args__ = (
        CheckConstraint("price >= 0", name="price_non_negative"),
        CheckConstraint("duration_days > 0", name="duration_positive"),
        CheckConstraint("visit_limit IS NULL OR visit_limit > 0", name="visit_limit_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    type: Mapped[TariffType] = mapped_column(str_enum(TariffType))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    duration_days: Mapped[int]
    visit_limit: Mapped[int | None] = mapped_column(comment="NULL means unlimited visits")
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)

    memberships: Mapped[list[Membership]] = relationship(back_populates="tariff_plan")


class MembershipOption(Base):
    """Paid add-on to a membership: sauna, locker, towel and so on."""

    __tablename__ = "membership_options"
    __table_args__ = (CheckConstraint("price >= 0", name="price_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(default=True)
