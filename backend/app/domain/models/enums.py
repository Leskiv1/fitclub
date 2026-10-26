"""Enumerations of the domain and a helper to store them as checked strings in the database."""

from enum import StrEnum

from sqlalchemy import Enum


class Role(StrEnum):
    CLIENT = "client"
    TRAINER = "trainer"
    RECEPTION = "reception"
    ADMIN = "admin"


class TariffType(StrEnum):
    SINGLE_VISIT = "single_visit"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    VISIT_PACK = "visit_pack"


class MembershipStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    FROZEN = "frozen"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PaymentMethod(StrEnum):
    CASH = "cash"
    CARD = "card"
    ONLINE = "online"


class PaymentStatus(StrEnum):
    PAID = "paid"
    FAILED = "failed"


class SessionKind(StrEnum):
    GROUP = "group"
    INDIVIDUAL = "individual"


class BookingStatus(StrEnum):
    BOOKED = "booked"
    CANCELLED = "cancelled"
    ATTENDED = "attended"


class DiscountType(StrEnum):
    STUDENT = "student"
    LOYALTY = "loyalty"
    PROMO = "promo"


class NotificationChannel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


def str_enum(enum_cls: type[StrEnum]) -> Enum:
    """Column type: a VARCHAR with a CHECK constraint instead of a native PostgreSQL enum."""
    return Enum(
        enum_cls,
        name=enum_cls.__name__.lower(),
        native_enum=False,
        create_constraint=True,
        length=max(len(member.value) for member in enum_cls),
        values_callable=lambda cls: [member.value for member in cls],
    )
