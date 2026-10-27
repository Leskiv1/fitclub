from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.models.enums import (
    NotificationChannel,
    NotificationKind,
    NotificationStatus,
    str_enum,
)

if TYPE_CHECKING:
    from app.domain.models.client import Client
    from app.domain.models.membership import Membership


class Notification(Base):
    """Message sent to a client, e.g. about an expiring membership (Ф-6)."""

    __tablename__ = "notifications"
    __table_args__ = (
        # one notification of each kind per membership: protects against duplicates from parallel workers
        Index(
            "uq_notifications_membership_kind",
            "membership_id",
            "kind",
            unique=True,
            postgresql_where=text("membership_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    membership_id: Mapped[int | None] = mapped_column(ForeignKey("memberships.id", ondelete="CASCADE"))
    kind: Mapped[NotificationKind] = mapped_column(str_enum(NotificationKind))
    channel: Mapped[NotificationChannel] = mapped_column(str_enum(NotificationChannel))
    subject: Mapped[str | None] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[NotificationStatus] = mapped_column(
        str_enum(NotificationStatus), default=NotificationStatus.PENDING
    )
    error: Mapped[str | None] = mapped_column(String(300), comment="Why delivery failed")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped[Client] = relationship(back_populates="notifications")
    membership: Mapped[Membership | None] = relationship()
