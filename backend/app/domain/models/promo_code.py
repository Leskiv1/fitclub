from __future__ import annotations

from datetime import date

from sqlalchemy import CheckConstraint, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PromoCode(Base):
    """Promotional code that gives a percentage discount on a membership purchase."""

    __tablename__ = "promo_codes"
    __table_args__ = (CheckConstraint("percent BETWEEN 1 AND 90", name="percent_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    percent: Mapped[int]
    valid_until: Mapped[date | None] = mapped_column(Date, comment="NULL means no end date")
    is_active: Mapped[bool] = mapped_column(default=True)

    def is_usable(self, on: date) -> bool:
        return self.is_active and (self.valid_until is None or on <= self.valid_until)
