from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.domain.models.training import TrainingSession


class Hall(Base):
    """Training hall of the club."""

    __tablename__ = "halls"
    __table_args__ = (CheckConstraint("capacity > 0", name="capacity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    capacity: Mapped[int]

    sessions: Mapped[list[TrainingSession]] = relationship(back_populates="hall")

    def is_free(self, start: datetime, end: datetime) -> bool:
        return not any(session.overlaps(start, end) for session in self.sessions)
