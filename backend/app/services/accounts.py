"""Helpers shared by services that create people together with their user account."""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.domain.errors import ConflictError
from app.domain.models import Role, User
from app.repositories.users import UserRepository


class AccountRegistry:
    """Creates user accounts and keeps e-mail addresses unique (case-insensitive)."""

    def __init__(self, session: Session) -> None:
        self.users = UserRepository(session)

    def ensure_email_free(self, email: str, current: User | None = None) -> None:
        existing = self.users.get_by_email(email)
        if existing is not None and existing is not current:
            raise ConflictError(f"Користувач з email «{email}» вже існує")

    def new_user(self, email: str, password: str, role: Role) -> User:
        self.ensure_email_free(email)
        return User(email=email.lower(), password_hash=hash_password(password), role=role)
