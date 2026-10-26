from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.domain.models import Client, Membership, Visit
from app.repositories.base import BaseRepository


class VisitRepository(BaseRepository[Visit]):
    model = Visit

    def for_client_page(self, client_id: int, *, offset: int, limit: int) -> tuple[Sequence[Visit], int]:
        """Visit history of a client (Ф-2), newest first."""
        query = (
            select(Visit)
            .join(Membership, Visit.membership_id == Membership.id)
            .where(Membership.client_id == client_id)
            .options(joinedload(Visit.membership).joinedload(Membership.tariff_plan))
            .order_by(Visit.checked_in_at.desc())
        )
        return self._page(query, offset, limit)

    def client_visit_on(self, client_id: int, day: date) -> Visit | None:
        query = (
            select(Visit)
            .join(Membership, Visit.membership_id == Membership.id)
            .where(Membership.client_id == client_id, Visit.visit_date == day)
            .limit(1)
        )
        return self.session.scalar(query)

    def on_day(self, day: date) -> Sequence[Visit]:
        """Everyone who came to the club on a local day, latest arrival first."""
        query = (
            select(Visit)
            .where(Visit.visit_date == day)
            .options(
                joinedload(Visit.membership).joinedload(Membership.client).joinedload(Client.user),
                joinedload(Visit.membership).joinedload(Membership.tariff_plan),
            )
            .order_by(Visit.checked_in_at.desc())
        )
        return self.session.scalars(query).unique().all()
