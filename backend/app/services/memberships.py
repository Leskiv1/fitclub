"""Operations on existing memberships and the promo code catalog."""

from collections.abc import Sequence
from datetime import date

from sqlalchemy.orm import Session

from app.domain.errors import ConflictError, NotFoundError
from app.domain.models import Membership, PromoCode
from app.repositories.clients import ClientRepository
from app.repositories.memberships import MembershipRepository, PromoCodeRepository
from app.services.crud import CrudService


class MembershipService:
    """Freezing, unfreezing and cancelling go through the membership's State object."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.memberships = MembershipRepository(session)
        self.clients = ClientRepository(session)

    def get(self, membership_id: int) -> Membership:
        membership = self.memberships.get(membership_id)
        if membership is None:
            raise NotFoundError("Абонемент", membership_id)
        return membership

    def history(self, client_id: int) -> Sequence[Membership]:
        if self.clients.get(client_id) is None:
            raise NotFoundError("Клієнт", client_id)
        return self.memberships.for_client(client_id)

    def freeze(self, membership_id: int, on: date | None = None) -> Membership:
        membership = self.get(membership_id)
        membership.freeze(on or date.today())
        self.session.commit()
        return membership

    def unfreeze(self, membership_id: int, on: date | None = None) -> Membership:
        membership = self.get(membership_id)
        membership.unfreeze(on or date.today())
        self.session.commit()
        return membership

    def cancel(self, membership_id: int) -> Membership:
        membership = self.get(membership_id)
        membership.cancel()
        self.session.commit()
        return membership


class PromoCodeService(CrudService[PromoCode]):
    """GoF: Template Method — ConcreteClass."""

    entity_name = "Промокод"
    unique_fields = ("code",)
    repository: PromoCodeRepository

    def __init__(self, session: Session) -> None:
        super().__init__(session, PromoCodeRepository(session))

    def _ensure_deletable(self, entity: PromoCode) -> None:
        if self.repository.is_in_use(entity.code):
            raise ConflictError("Промокод вже використано в покупках — деактивуйте його замість видалення")
