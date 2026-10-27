from collections.abc import Sequence
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import aliased, selectinload

from app.domain.models import (
    Membership,
    MembershipStatus,
    Notification,
    NotificationKind,
    Payment,
    PaymentStatus,
    PromoCode,
)
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

    def overdue(self, today: date) -> Sequence[Membership]:
        """Memberships still marked active although their period is over."""
        query = select(Membership).where(
            Membership.status == MembershipStatus.ACTIVE, Membership.end_date < today
        )
        return self.session.scalars(query).all()

    def reminder_candidates(self, today: date, until: date) -> Sequence[Membership]:
        """Active memberships ending in [today, until] whose client got no reminder yet and did not renew."""
        renewal = aliased(Membership)
        renewed = (
            select(renewal.id)
            .where(
                renewal.client_id == Membership.client_id,
                renewal.id != Membership.id,
                renewal.status.in_(
                    [MembershipStatus.ACTIVE, MembershipStatus.PENDING, MembershipStatus.FROZEN]
                ),
                renewal.end_date > Membership.end_date,
            )
            .exists()
        )
        reminded = (
            select(Notification.id)
            .where(
                Notification.membership_id == Membership.id,
                Notification.kind == NotificationKind.MEMBERSHIP_EXPIRING,
            )
            .exists()
        )
        query = (
            select(Membership)
            .where(
                Membership.status == MembershipStatus.ACTIVE,
                Membership.end_date.between(today, until),
                ~renewed,
                ~reminded,
            )
            .order_by(Membership.end_date, Membership.id)
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

    def covering(self, client_id: int, day: date, *, lock: bool = False) -> Sequence[Membership]:
        """Non-cancelled memberships of a client whose period includes `day`.

        With `lock=True` the rows are locked (SELECT ... FOR UPDATE) until the transaction ends, so two
        simultaneous check-ins of the same client are processed one after another.
        """
        query = select(Membership).where(
            Membership.client_id == client_id,
            Membership.status != MembershipStatus.CANCELLED,
            Membership.start_date <= day,
            Membership.end_date >= day,
        )
        if lock:
            query = query.with_for_update()
        return self.session.scalars(query.order_by(Membership.id)).all()

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
