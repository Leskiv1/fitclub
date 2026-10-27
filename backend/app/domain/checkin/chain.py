"""Entry checks performed before a visit is registered (Ф-2)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from app.domain.errors import BusinessRuleError
from app.domain.models import Client, Membership, MembershipStatus, Visit

# When a client has several memberships for today, the one that can let them in is chosen first
_STATUS_PRIORITY = {
    MembershipStatus.ACTIVE: 0,
    MembershipStatus.FROZEN: 1,
    MembershipStatus.PENDING: 2,
    MembershipStatus.EXPIRED: 3,
}


class SupportsOpeningHours(Protocol):
    """Club settings as the chain needs them (a DB row or its cached snapshot)."""

    def is_open(self, moment: datetime) -> bool: ...


class CheckInDeniedError(BusinessRuleError):
    """Entry refused; `code` tells the reception why (shown next to the client's card)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CheckInContext:
    client: Client
    memberships: list[Membership]  # non-cancelled memberships that cover today
    settings: SupportsOpeningHours
    now: datetime
    visit_today: Visit | None

    @property
    def today(self) -> date:
        return self.now.date()

    @property
    def membership(self) -> Membership | None:
        """The membership the visit will be counted against."""
        if not self.memberships:
            return None
        return min(self.memberships, key=lambda m: (_STATUS_PRIORITY[m.status], m.end_date))


class CheckInHandler(ABC):
    """GoF: Chain of Responsibility — Handler.

    Each handler checks one condition: it either refuses entry (raises) or passes the request on.
    """

    def __init__(self) -> None:
        self._next: CheckInHandler | None = None

    def set_next(self, handler: CheckInHandler) -> CheckInHandler:
        self._next = handler
        return handler  # allows a.set_next(b).set_next(c)

    def handle(self, context: CheckInContext) -> None:
        self.check(context)
        if self._next is not None:
            self._next.handle(context)

    @abstractmethod
    def check(self, context: CheckInContext) -> None: ...


class HasMembershipHandler(CheckInHandler):
    """GoF: Chain of Responsibility — ConcreteHandler."""

    def check(self, context: CheckInContext) -> None:
        if context.membership is None:
            raise CheckInDeniedError("no_membership", "У клієнта немає абонемента, що діє сьогодні")


class MembershipActiveHandler(CheckInHandler):
    """GoF: Chain of Responsibility — ConcreteHandler."""

    REASONS = {
        MembershipStatus.FROZEN: ("membership_frozen", "Абонемент заморожено"),
        MembershipStatus.PENDING: ("membership_pending", "Абонемент не оплачено"),
        MembershipStatus.EXPIRED: ("membership_expired", "Абонемент закінчився"),
    }

    def check(self, context: CheckInContext) -> None:
        status = context.membership.status
        if status != MembershipStatus.ACTIVE:
            raise CheckInDeniedError(*self.REASONS[status])


class VisitsLeftHandler(CheckInHandler):
    """GoF: Chain of Responsibility — ConcreteHandler."""

    def check(self, context: CheckInContext) -> None:
        if context.membership.visits_left == 0:
            raise CheckInDeniedError("no_visits_left", "За абонементом не лишилось відвідувань")


class ClubOpenHandler(CheckInHandler):
    """GoF: Chain of Responsibility — ConcreteHandler."""

    def check(self, context: CheckInContext) -> None:
        if not context.settings.is_open(context.now):
            raise CheckInDeniedError("club_closed", f"Клуб зараз зачинений ({context.now:%H:%M})")


class NotCheckedInTodayHandler(CheckInHandler):
    """GoF: Chain of Responsibility — ConcreteHandler. A repeated scan must not use up a second visit."""

    def check(self, context: CheckInContext) -> None:
        if context.visit_today is not None:
            local_time = context.visit_today.checked_in_at.astimezone(context.now.tzinfo)  # DB returns UTC
            raise CheckInDeniedError(
                "already_checked_in", f"Клієнта вже відмічено сьогодні о {local_time:%H:%M}"
            )


def build_check_in_chain() -> CheckInHandler:
    """The order matters: the reason shown is the first problem found, from the most fundamental one."""
    head = HasMembershipHandler()
    (
        head.set_next(MembershipActiveHandler())
        .set_next(VisitsLeftHandler())
        .set_next(ClubOpenHandler())
        .set_next(NotCheckedInTodayHandler())
    )
    return head
