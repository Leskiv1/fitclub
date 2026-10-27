"""Sign-in and self-registration of clients."""

from sqlalchemy.orm import Session

from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.domain.errors import AuthenticationError
from app.domain.models import Client, User
from app.repositories.users import UserRepository
from app.schemas.clients import ClientCreate
from app.services.clients import ClientService

WRONG_CREDENTIALS = "Невірний email або пароль"
_DUMMY_HASH = hash_password("timing-equalizer")


class AuthService:
    """GRASP Controller for authentication use cases: login, registration, resolving a token."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def login(self, email: str, password: str) -> tuple[User, str, int]:
        user = self.users.get_by_email(email)
        # The same message and (thanks to the dummy check) the same timing for an unknown e-mail
        # and a wrong password, so the endpoint does not reveal which accounts exist
        if user is None:
            verify_password(password, _DUMMY_HASH)
            raise AuthenticationError(WRONG_CREDENTIALS)
        if not user.authenticate(password):
            raise AuthenticationError(WRONG_CREDENTIALS)
        token, expires_in = create_access_token(user.id, user.role)
        return user, token, expires_in

    def register_client(self, data: ClientCreate) -> tuple[Client, str, int]:
        """A guest signs up and is signed in right away."""
        client = ClientService(self.session).create(data)
        token, expires_in = create_access_token(client.user.id, client.user.role)
        return client, token, expires_in

    def user_from_token(self, token: str) -> User:
        """The user is re-read on every request, so a deactivated account loses access immediately."""
        try:
            payload = decode_access_token(token)
        except InvalidTokenError as exc:
            raise AuthenticationError("Токен недійсний або прострочений, увійдіть знову") from exc
        user = self.users.get(payload.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Обліковий запис не знайдено або деактивовано")
        return user
