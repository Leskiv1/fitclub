from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.security import verify_password
from app.domain.models.enums import Role, str_enum

if TYPE_CHECKING:
    from app.domain.models.client import Client
    from app.domain.models.trainer import Trainer


class User(Base):
    """Account used to sign in; its role decides what the user may do."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(str_enum(Role))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped[Client | None] = relationship(back_populates="user")
    trainer: Mapped[Trainer | None] = relationship(back_populates="user")

    def authenticate(self, password: str) -> bool:
        return self.is_active and verify_password(password, self.password_hash)

    def has_role(self, role: Role) -> bool:
        return self.role == role
