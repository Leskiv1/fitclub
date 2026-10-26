from collections.abc import Sequence
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.domain.models import Membership, MembershipStatus, Payment, PaymentStatus, PromoCode
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

    def for_client(self, client_id: int) -> Sequence[Membership]:
        """Membership history, newest first."""
        query = (
            select(Membership)
            .where(Membership.client_id == client_id)
            .options(
                selectinload(Membership.tariff_plan),
                selectinload(Membership.options),
                selectinload(Membership.payment),
            )
            .order_by(Membership.start_date.desc(), Membership.id.desc())
        )
        return self.session.scalars(query).all()

    def latest_running(self, client_id: int, on: date) -> Membership | None:
        """The active or frozen membership that lasts the longest from `on` — a new purchase continues it."""
        query = (
            select(Membership)
            .where(
                Membership.client_id == client_id,
                Membership.status.in_([MembershipStatus.ACTIVE, MembershipStatus.FROZEN]),
                Membership.end_date >= on,
            )
            .order_by(Membership.end_date.desc())
            .limit(1)
        )
        return self.session.scalar(query)

    def count_paid(self, client_id: int) -> int:
        query = (
            select(func.count(Payment.id))
            .join(Membership, Payment.membership_id == Membership.id)
            .where(Membership.client_id == client_id, Payment.status == PaymentStatus.PAID)
        )
        return self.session.scalar(query) or 0


class PromoCodeRepository(BaseRepository[PromoCode]):
    model = PromoCode

    def get_by_code(self, code: str) -> PromoCode | None:
        return self.session.scalar(
            select(PromoCode).where(func.upper(PromoCode.code) == code.strip().upper())
        )

    def is_in_use(self, code: str) -> bool:
        query = select(Membership.id).where(func.upper(Membership.discount_reference) == code.upper())
        return self._exists(query)
