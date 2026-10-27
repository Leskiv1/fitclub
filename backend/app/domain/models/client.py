from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.models.enums import NotificationChannel, str_enum

if TYPE_CHECKING:
    from app.domain.models.booking import Booking
    from app.domain.models.membership import Membership
    from app.domain.models.notification import Notification
    from app.domain.models.user import User
    from app.domain.models.visit import Visit


class Client(Base):
    """Club member (Ф-1): personal data, memberships and visit history."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name: Mapped[str] = mapped_column(String(150), index=True)
    birth_date: Mapped[date] = mapped_column(Date)
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    notification_channel: Mapped[NotificationChannel] = mapped_column(
        str_enum(NotificationChannel), default=NotificationChannel.EMAIL
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="client")
    memberships: Mapped[list[Membership]] = relationship(
        back_populates="client", order_by="Membership.start_date"
    )
    bookings: Mapped[list[Booking]] = relationship(back_populates="client")
    notifications: Mapped[list[Notification]] = relationship(back_populates="client")

    def age(self, today: date | None = None) -> int:
        today = today or date.today()
        had_birthday = (today.month, today.day) >= (self.birth_date.month, self.birth_date.day)
        return today.year - self.birth_date.year - (0 if had_birthday else 1)

    def active_membership(self, on: date | None = None) -> Membership | None:
        """The membership that currently lets the client in, if any (the latest one wins)."""
        valid = [membership for membership in self.memberships if membership.is_valid(on)]
        return valid[-1] if valid else None

    def visit_history(self) -> list[Visit]:
        visits = [visit for membership in self.memberships for visit in membership.visits]
        return sorted(visits, key=lambda visit: visit.checked_in_at, reverse=True)
