from collections.abc import Sequence
from datetime import date

from sqlalchemy import select

from app.domain.models import Membership, MembershipStatus
from app.repositories.base import BaseRepository


class MembershipRepository(BaseRepository[Membership]):
    model = Membership

    def expiring_between(self, start: date, end: date) -> Sequence[Membership]:
        """Active memberships whose end date falls into [start, end] — candidates for a reminder (Ф-6)."""
        query = (
            select(Membership)
            .where(
                Membership.status == MembershipStatus.ACTIVE,
                Membership.end_date.between(start, end),
            )
            .order_by(Membership.end_date)
        )
        return self.session.scalars(query).all()
