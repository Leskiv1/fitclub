from collections.abc import Sequence

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import selectinload

from app.domain.models import Client, Membership
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    model = Client

    def search(self, text: str, *, limit: int = 20) -> Sequence[Client]:
        """Find clients by part of the full name or phone number."""
        return self.session.scalars(self._search_query(text).limit(limit)).all()

    def search_page(self, text: str | None, *, offset: int, limit: int) -> tuple[Sequence[Client], int]:
        """Page of the client registry (Ф-1); memberships are loaded in one extra query, not per client."""
        query = self._search_query(text).options(
            selectinload(Client.user),
            selectinload(Client.memberships).selectinload(Membership.tariff_plan),
        )
        return self._page(query, offset, limit)

    def has_memberships(self, client_id: int) -> bool:
        return self._exists(select(Membership.id).where(Membership.client_id == client_id))

    @staticmethod
    def _search_query(text: str | None) -> Select:
        query = select(Client).order_by(Client.full_name, Client.id)
        if text and text.strip():
            pattern = f"%{text.strip()}%"
            query = query.where(or_(Client.full_name.ilike(pattern), Client.phone.ilike(pattern)))
        return query
