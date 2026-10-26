"""Catalog managed by the administrator (ЗВ-7): halls, tariff plans (Ф-5) and membership options."""

from sqlalchemy.orm import Session

from app.domain.errors import BusinessRuleError, ConflictError
from app.domain.models import Hall, MembershipOption, TariffPlan, TariffType
from app.repositories.halls import HallRepository
from app.repositories.tariffs import MembershipOptionRepository, TariffPlanRepository
from app.services.crud import CrudService


class HallService(CrudService[Hall]):
    """GoF: Template Method — ConcreteClass."""

    entity_name = "Зал"
    unique_fields = ("name",)
    repository: HallRepository

    def __init__(self, session: Session) -> None:
        super().__init__(session, HallRepository(session))

    def _ensure_deletable(self, entity: Hall) -> None:
        if self.repository.is_in_use(entity.id):
            raise ConflictError("У залі заплановані або проведені заняття — видалити його не можна")


class TariffPlanService(CrudService[TariffPlan]):
    """GoF: Template Method — ConcreteClass."""

    entity_name = "Тариф"
    unique_fields = ("name",)
    repository: TariffPlanRepository

    def __init__(self, session: Session) -> None:
        super().__init__(session, TariffPlanRepository(session))

    def _validate(self, entity: TariffPlan) -> None:
        if entity.type == TariffType.SINGLE_VISIT and entity.visit_limit != 1:
            raise BusinessRuleError("Разовий тариф має дозволяти рівно одне відвідування")
        if entity.type == TariffType.VISIT_PACK and entity.visit_limit is None:
            raise BusinessRuleError("Для пакета відвідувань потрібно вказати кількість відвідувань")

    def _ensure_deletable(self, entity: TariffPlan) -> None:
        if self.repository.is_in_use(entity.id):
            raise ConflictError("За тарифом вже оформлені абонементи — деактивуйте його замість видалення")


class MembershipOptionService(CrudService[MembershipOption]):
    """GoF: Template Method — ConcreteClass."""

    entity_name = "Опція"
    unique_fields = ("name",)
    repository: MembershipOptionRepository

    def __init__(self, session: Session) -> None:
        super().__init__(session, MembershipOptionRepository(session))

    def _ensure_deletable(self, entity: MembershipOption) -> None:
        if self.repository.is_in_use(entity.id):
            raise ConflictError("Опцію вже додано до абонементів — деактивуйте її замість видалення")
