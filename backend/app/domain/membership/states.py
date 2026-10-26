"""Membership life cycle: Pending → Active ⇄ Frozen; Active → Expired; Pending/Active/Frozen → Cancelled."""

from datetime import date, datetime, timedelta

from app.domain.errors import BusinessRuleError
from app.domain.membership.factories import factory_for
from app.domain.models import Membership, MembershipStatus, Visit


class MembershipState:
    """GoF: State — State. Every action is forbidden by default; concrete states allow their transitions."""

    status: MembershipStatus
    label: str

    def activate(self, membership: Membership) -> None:
        self._forbid("активувати")

    def check_in(self, membership: Membership, moment: datetime) -> Visit:
        self._forbid("зареєструвати відвідування за")

    def freeze(self, membership: Membership, on: date) -> None:
        self._forbid("заморозити")

    def unfreeze(self, membership: Membership, on: date) -> None:
        self._forbid("розморозити")

    def cancel(self, membership: Membership) -> None:
        self._forbid("скасувати")

    def expire(self, membership: Membership) -> None:
        self._forbid("завершити")

    def _forbid(self, action: str):
        raise BusinessRuleError(f"Неможливо {action} абонемент: він {self.label}")


class PendingState(MembershipState):
    """GoF: State — ConcreteState "Pending": created but not paid yet."""

    status = MembershipStatus.PENDING
    label = "очікує оплати"

    def activate(self, membership: Membership) -> None:
        membership.status = MembershipStatus.ACTIVE

    def cancel(self, membership: Membership) -> None:
        membership.status = MembershipStatus.CANCELLED


class ActiveState(MembershipState):
    """GoF: State — ConcreteState "Active": the only state that lets the client in."""

    status = MembershipStatus.ACTIVE
    label = "активний"

    def check_in(self, membership: Membership, moment: datetime) -> Visit:
        day = moment.date()
        if day < membership.start_date:
            raise BusinessRuleError(f"Абонемент починає діяти з {membership.start_date:%d.%m.%Y}")
        if day > membership.end_date:
            raise BusinessRuleError(f"Термін дії абонемента закінчився {membership.end_date:%d.%m.%Y}")
        if membership.visits_left == 0:
            raise BusinessRuleError("За абонементом не лишилось відвідувань")

        # moment is in the club's time zone, so its date is the local day of the visit
        visit = Visit(membership=membership, checked_in_at=moment, visit_date=moment.date())
        if membership.visits_left is not None:
            membership.visits_left -= 1
            if membership.visits_left == 0:
                membership.status = MembershipStatus.EXPIRED  # the last visit of a pack ends the membership
        return visit

    def freeze(self, membership: Membership, on: date) -> None:
        factory = factory_for(membership.tariff_plan.type)
        if not factory.freezable:
            raise BusinessRuleError("Абонемент цього типу не можна заморозити")
        if membership.frozen_days >= factory.max_freeze_days:
            raise BusinessRuleError(f"Ліміт заморозки ({factory.max_freeze_days} днів) уже використано")
        if not membership.start_date <= on <= membership.end_date:
            raise BusinessRuleError("Заморозити можна лише абонемент, що діє на цю дату")
        membership.frozen_at = on
        membership.status = MembershipStatus.FROZEN

    def cancel(self, membership: Membership) -> None:
        membership.status = MembershipStatus.CANCELLED

    def expire(self, membership: Membership) -> None:
        membership.status = MembershipStatus.EXPIRED


class FrozenState(MembershipState):
    """GoF: State — ConcreteState "Frozen": the validity period is paused."""

    status = MembershipStatus.FROZEN
    label = "заморожений"

    def unfreeze(self, membership: Membership, on: date) -> None:
        factory = factory_for(membership.tariff_plan.type)
        frozen_for = max(0, (on - membership.frozen_at).days)
        # the end date moves by the days spent frozen, but not beyond the freeze limit
        extension = min(frozen_for, factory.max_freeze_days - membership.frozen_days)
        membership.end_date += timedelta(days=extension)
        membership.frozen_days += extension
        membership.frozen_at = None
        membership.status = MembershipStatus.ACTIVE

    def cancel(self, membership: Membership) -> None:
        membership.frozen_at = None
        membership.status = MembershipStatus.CANCELLED


class ExpiredState(MembershipState):
    """GoF: State — ConcreteState "Expired": final, nothing is allowed."""

    status = MembershipStatus.EXPIRED
    label = "закінчився"


class CancelledState(MembershipState):
    """GoF: State — ConcreteState "Cancelled": final, nothing is allowed."""

    status = MembershipStatus.CANCELLED
    label = "скасований"


_STATES = {
    state.status: state
    for state in (PendingState(), ActiveState(), FrozenState(), ExpiredState(), CancelledState())
}


def state_for(status: MembershipStatus) -> MembershipState:
    return _STATES[status]
