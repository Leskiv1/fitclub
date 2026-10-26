"""Password hashing (bcrypt) and access tokens (JWT).

The rest of the code depends only on these functions, so the hashing algorithm or token format
can change here without touching services and routers (GRASP: Protected Variations).
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


@dataclass(frozen=True)
class TokenPayload:
    user_id: int
    role: str


class InvalidTokenError(Exception):
    """The token is malformed, has a wrong signature or has expired."""


def create_access_token(user_id: int, role: str) -> tuple[str, int]:
    """Signed JWT and its lifetime in seconds."""
    settings = get_settings()
    now = datetime.now(UTC)
    expires_in = settings.jwt_expire_minutes * 60
    claims = {"sub": str(user_id), "role": role, "iat": now, "exp": now + timedelta(seconds=expires_in)}
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm), expires_in


def decode_access_token(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp"]},
        )
        return TokenPayload(user_id=int(claims["sub"]), role=claims.get("role", ""))
    except (jwt.PyJWTError, ValueError) as exc:
        raise InvalidTokenError(str(exc)) from exc
