"""Creation of memberships: every tariff type has its own rules for dates and visits."""

import calendar
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import date, timedelta

from app.domain.models import (
    Client,
    Membership,
    MembershipOption,
    MembershipStatus,
    TariffPlan,
    TariffType,
)


def add_months(day: date, months: int) -> date:
    """Calendar arithmetic: 31 Jan + 1 month = 28/29 Feb (the last day of a shorter month)."""
    month_index = day.month - 1 + months
    year, month = day.year + month_index // 12, month_index % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


class MembershipFactory(ABC):
    """GoF: Factory Method — Creator.

    `issue()` is the operation that uses the factory method `create_membership()`; subclasses decide how a
    membership of their tariff type is built (validity period and visit limit) and whether it can be frozen.
    """

    freezable: bool = False
    max_freeze_days: int = 0

    def issue(
        self, client: Client, tariff: TariffPlan, start: date, options: Iterable[MembershipOption] = ()
    ) -> Membership:
        membership = self.create_membership(tariff, start)
        # relationships are attached only here, so a quote (create_membership alone) never enters the session
        membership.client = client
        membership.tariff_plan = tariff
        membership.options = list(options)
        return membership

    @abstractmethod
    def create_membership(self, tariff: TariffPlan, start: date) -> Membership:
        """Factory method: a new, not yet paid membership with its dates and visit limit."""

    @staticmethod
    def _new(tariff: TariffPlan, start: date, end: date, visits_left: int | None) -> Membership:
        return Membership(
            tariff_plan_id=tariff.id,
            start_date=start,
            end_date=end,
            visits_left=visits_left,
            status=MembershipStatus.PENDING,
            frozen_days=0,
        )


class SingleVisitMembershipFactory(MembershipFactory):
    """GoF: Factory Method — ConcreteCreator. One visit, valid only on the day of purchase."""

    def create_membership(self, tariff: TariffPlan, start: date) -> Membership:
        return self._new(tariff, start, start, visits_left=1)


class MonthlyMembershipFactory(MembershipFactory):
    """GoF: Factory Method — ConcreteCreator. A calendar month, optionally with a visit limit."""

    freezable = True
    max_freeze_days = 30

    def create_membership(self, tariff: TariffPlan, start: date) -> Membership:
        end = add_months(start, 1) - timedelta(days=1)
        return self._new(tariff, start, end, visits_left=tariff.visit_limit)


class YearlyMembershipFactory(MembershipFactory):
    """GoF: Factory Method — ConcreteCreator. A calendar year (29 Feb is handled), unlimited visits."""

    freezable = True
    max_freeze_days = 30

    def create_membership(self, tariff: TariffPlan, start: date) -> Membership:
        end = add_months(start, 12) - timedelta(days=1)
        return self._new(tariff, start, end, visits_left=tariff.visit_limit)


class VisitPackMembershipFactory(MembershipFactory):
    """GoF: Factory Method — ConcreteCreator. N visits within the tariff's number of days."""

    def create_membership(self, tariff: TariffPlan, start: date) -> Membership:
        end = start + timedelta(days=tariff.duration_days - 1)
        return self._new(tariff, start, end, visits_left=tariff.visit_limit)


_FACTORIES: dict[TariffType, MembershipFactory] = {
    TariffType.SINGLE_VISIT: SingleVisitMembershipFactory(),
    TariffType.MONTHLY: MonthlyMembershipFactory(),
    TariffType.YEARLY: YearlyMembershipFactory(),
    TariffType.VISIT_PACK: VisitPackMembershipFactory(),
}


def factory_for(tariff_type: TariffType) -> MembershipFactory:
    """Picks the concrete creator for a tariff type; a new type needs only a new factory class here."""
    return _FACTORIES[tariff_type]
