"""Membership purchase (Ф-5), history and life cycle; promo codes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import (
    ADMIN_ONLY,
    STAFF_ONLY,
    STAFF_ROLES,
    ClockDep,
    CurrentUser,
    DbSession,
    EventBusDep,
    Pagination,
    ensure_can_view_client,
)
from app.api.errors import ERROR_RESPONSES
from app.domain.errors import BusinessRuleError, PermissionDeniedError
from app.domain.models import PaymentMethod, Role, User
from app.schemas.common import Page
from app.schemas.memberships import (
    MembershipRead,
    PromoCodeCreate,
    PromoCodeRead,
    PromoCodeUpdate,
    PurchaseIn,
    QuoteIn,
    QuoteOut,
)
from app.services.membership_purchase import DiscountRequest, MembershipPurchaseFacade, PurchaseRequest
from app.services.memberships import MembershipService, PromoCodeService

router = APIRouter(tags=["Абонементи"], responses=ERROR_RESPONSES)
promo_codes = APIRouter(prefix="/promo-codes", tags=["Промокоди"], responses=ERROR_RESPONSES)


def get_purchase_facade(db: DbSession, clock: ClockDep, events: EventBusDep) -> MembershipPurchaseFacade:
    return MembershipPurchaseFacade(db, clock=clock, events=events)


def get_membership_service(db: DbSession) -> MembershipService:
    return MembershipService(db)


def get_promo_code_service(db: DbSession) -> PromoCodeService:
    return PromoCodeService(db)


PurchaseFacadeDep = Annotated[MembershipPurchaseFacade, Depends(get_purchase_facade)]
MembershipServiceDep = Annotated[MembershipService, Depends(get_membership_service)]
PromoCodeServiceDep = Annotated[PromoCodeService, Depends(get_promo_code_service)]


def _to_request(data: QuoteIn, user: User) -> PurchaseRequest:
    """A client buys only for themselves and only online; staff buy for the client given in the body."""
    if user.role == Role.CLIENT:
        if user.client is None or data.client_id not in (None, user.client.id):
            raise PermissionDeniedError("Клієнт може оформити абонемент лише для себе")
        client_id = user.client.id
    elif user.role in STAFF_ROLES:
        if data.client_id is None:
            raise BusinessRuleError("Вкажіть клієнта, для якого оформлюється абонемент")
        client_id = data.client_id
    else:
        raise PermissionDeniedError()

    payment_method = getattr(data, "payment_method", PaymentMethod.ONLINE)
    if user.role == Role.CLIENT and payment_method != PaymentMethod.ONLINE:
        raise BusinessRuleError("Готівкою або карткою на касі можна оплатити лише на рецепції")
    discount = DiscountRequest(data.discount.type, data.discount.reference) if data.discount else None
    return PurchaseRequest(
        client_id=client_id,
        tariff_id=data.tariff_id,
        option_ids=data.option_ids,
        discount=discount,
        start_date=data.start_date,
        payment_method=payment_method,
    )


@router.post("/memberships/quote", summary="Розрахувати вартість абонемента (без оформлення)")
def quote_membership(data: QuoteIn, user: CurrentUser, facade: PurchaseFacadeDep) -> QuoteOut:
    return QuoteOut.from_quote(facade.quote(_to_request(data, user)))


@router.post("/memberships", status_code=status.HTTP_201_CREATED, summary="Оформити й оплатити абонемент")
def purchase_membership(data: PurchaseIn, user: CurrentUser, facade: PurchaseFacadeDep) -> MembershipRead:
    return MembershipRead.from_model(facade.purchase(_to_request(data, user)))


@router.get("/clients/{client_id}/memberships", summary="Історія абонементів клієнта")
def client_memberships(
    client_id: int, user: CurrentUser, service: MembershipServiceDep
) -> list[MembershipRead]:
    ensure_can_view_client(user, client_id)
    return [MembershipRead.from_model(m) for m in service.history(client_id)]


@router.get("/memberships/{membership_id}", summary="Абонемент")
def get_membership(membership_id: int, user: CurrentUser, service: MembershipServiceDep) -> MembershipRead:
    membership = service.get(membership_id)
    ensure_can_view_client(user, membership.client_id)
    return MembershipRead.from_model(membership)


@router.post("/memberships/{membership_id}/freeze", summary="Заморозити (персонал)", dependencies=STAFF_ONLY)
def freeze_membership(membership_id: int, service: MembershipServiceDep) -> MembershipRead:
    return MembershipRead.from_model(service.freeze(membership_id))


@router.post(
    "/memberships/{membership_id}/unfreeze", summary="Розморозити (персонал)", dependencies=STAFF_ONLY
)
def unfreeze_membership(membership_id: int, service: MembershipServiceDep) -> MembershipRead:
    return MembershipRead.from_model(service.unfreeze(membership_id))


@router.post("/memberships/{membership_id}/cancel", summary="Скасувати (персонал)", dependencies=STAFF_ONLY)
def cancel_membership(membership_id: int, service: MembershipServiceDep) -> MembershipRead:
    return MembershipRead.from_model(service.cancel(membership_id))


# --- promo codes (administrator) ---


@promo_codes.get("", summary="Список промокодів", dependencies=ADMIN_ONLY)
def list_promo_codes(service: PromoCodeServiceDep, page: Pagination) -> Page[PromoCodeRead]:
    items, total = service.page(offset=page.offset, limit=page.limit)
    return Page(items=[PromoCodeRead.model_validate(p) for p in items], total=total, **page.model_dump())


@promo_codes.post(
    "", status_code=status.HTTP_201_CREATED, summary="Створити промокод", dependencies=ADMIN_ONLY
)
def create_promo_code(data: PromoCodeCreate, service: PromoCodeServiceDep) -> PromoCodeRead:
    return PromoCodeRead.model_validate(service.create(data))


@promo_codes.patch("/{promo_id}", summary="Змінити промокод", dependencies=ADMIN_ONLY)
def update_promo_code(promo_id: int, data: PromoCodeUpdate, service: PromoCodeServiceDep) -> PromoCodeRead:
    return PromoCodeRead.model_validate(service.update(promo_id, data))


@promo_codes.delete(
    "/{promo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити промокод",
    dependencies=ADMIN_ONLY,
)
def delete_promo_code(promo_id: int, service: PromoCodeServiceDep) -> None:
    service.delete(promo_id)
