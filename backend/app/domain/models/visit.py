from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.domain.models.membership import Membership


class Visit(Base):
    """A registered arrival of a client at the club (Ф-2), counted against a membership."""

    __tablename__ = "visits"
    __table_args__ = (
        # one visit per membership per local day — also protects against two simultaneous check-ins
        UniqueConstraint("membership_id", "visit_date", name="uq_visits_membership_day"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    membership_id: Mapped[int] = mapped_column(ForeignKey("memberships.id", ondelete="CASCADE"), index=True)
    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    visit_date: Mapped[date] = mapped_column(Date, index=True, comment="Local date of the visit in the club")

    membership: Mapped[Membership] = relationship(back_populates="visits")
