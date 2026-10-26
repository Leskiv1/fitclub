"""Client registry (Ф-1)."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Session

from app.domain.errors import ConflictError
from app.domain.models import Client, Role
from app.repositories.clients import ClientRepository
from app.services.accounts import AccountRegistry
from app.services.crud import CrudService


class ClientService(CrudService[Client]):
    """GoF: Template Method — ConcreteClass; a client is created together with a user account."""

    entity_name = "Клієнт"
    unique_fields = ("phone",)
    repository: ClientRepository

    def __init__(self, session: Session) -> None:
        super().__init__(session, ClientRepository(session))
        self.accounts = AccountRegistry(session)

    def search(self, text: str | None, *, offset: int, limit: int) -> tuple[Sequence[Client], int]:
        return self.repository.search_page(text, offset=offset, limit=limit)

    def _build(self, values: dict[str, Any]) -> Client:
        user = self.accounts.new_user(values.pop("email"), values.pop("password"), Role.CLIENT)
        return Client(user=user, **values)

    def _apply(self, entity: Client, changes: dict[str, Any]) -> None:
        email = changes.pop("email", None)
        if email is not None:
            self.accounts.ensure_email_free(email, current=entity.user)
            entity.user.email = email.lower()
        super()._apply(entity, changes)

    def _ensure_deletable(self, entity: Client) -> None:
        if self.repository.has_memberships(entity.id):
            raise ConflictError("У клієнта є історія абонементів — видалення зіпсує звіти")

    def _remove(self, entity: Client) -> None:
        # the account is removed together with the client
        self.session.delete(entity)
        self.session.delete(entity.user)
        self.session.flush()
