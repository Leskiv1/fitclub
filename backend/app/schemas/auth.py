from pydantic import EmailStr, Field

from app.domain.models import Role, User
from app.schemas.common import Schema


class LoginRequest(Schema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class CurrentUserRead(Schema):
    """Who is signed in; client_id / trainer_id let the UI open the right cabinet."""

    id: int
    email: str
    role: Role
    full_name: str | None
    client_id: int | None
    trainer_id: int | None

    @classmethod
    def from_model(cls, user: User) -> CurrentUserRead:
        profile = user.client or user.trainer
        return cls(
            id=user.id,
            email=user.email,
            role=user.role,
            full_name=profile.full_name if profile else None,
            client_id=user.client.id if user.client else None,
            trainer_id=user.trainer.id if user.trainer else None,
        )


class TokenResponse(Schema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Скільки секунд дійсний токен")
    user: CurrentUserRead
