from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.models.enums import BookingStatus, str_enum

if TYPE_CHECKING:
    from app.domain.models.client import Client
    from app.domain.models.training import TrainingSession


class Booking(Base):
    """Client's booking for a training session."""

    __tablename__ = "bookings"
    __table_args__ = (
        # A client may rebook after cancelling, but cannot hold two active bookings for one session
        Index(
            "uq_bookings_active_client_session",
            "session_id",
            "client_id",
            unique=True,
            postgresql_where=text("status <> 'cancelled'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("training_sessions.id", ondelete="CASCADE"), index=True
    )
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    status: Mapped[BookingStatus] = mapped_column(str_enum(BookingStatus), default=BookingStatus.BOOKED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[TrainingSession] = relationship(back_populates="bookings")
    client: Mapped[Client] = relationship(back_populates="bookings")

    def cancel(self) -> None:
        self.status = BookingStatus.CANCELLED
