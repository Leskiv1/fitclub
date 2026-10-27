from sqlalchemy import select

from app.domain.models import Membership, MembershipOption, TariffPlan, membership_option_links
from app.repositories.base import BaseRepository


class TariffPlanRepository(BaseRepository[TariffPlan]):
    model = TariffPlan

    def is_in_use(self, tariff_id: int) -> bool:
        return self._exists(select(Membership.id).where(Membership.tariff_plan_id == tariff_id))


class MembershipOptionRepository(BaseRepository[MembershipOption]):
    model = MembershipOption

    def is_in_use(self, option_id: int) -> bool:
        return self._exists(
            select(membership_option_links.c.option_id).where(
                membership_option_links.c.option_id == option_id
            )
        )
