"""ORM models of the domain; importing this package registers all of them in Base.metadata."""

from app.domain.models.booking import Booking
from app.domain.models.booking_action import BookingAction
from app.domain.models.client import Client
from app.domain.models.club_settings import ClubSettings
from app.domain.models.enums import (
    BookingActionType,
    BookingStatus,
    DiscountType,
    MembershipStatus,
    NotificationChannel,
    NotificationStatus,
    PaymentMethod,
    PaymentStatus,
    Role,
    SessionKind,
    TariffType,
)
from app.domain.models.hall import Hall
from app.domain.models.membership import Membership, Payment, membership_option_links
from app.domain.models.notification import Notification
from app.domain.models.promo_code import PromoCode
from app.domain.models.tariff import MembershipOption, TariffPlan
from app.domain.models.trainer import Trainer, WorkShift
from app.domain.models.training import GroupSession, IndividualSession, TrainingSession
from app.domain.models.user import User
from app.domain.models.visit import Visit

__all__ = [
    "Booking",
    "BookingAction",
    "BookingActionType",
    "BookingStatus",
    "Client",
    "ClubSettings",
    "DiscountType",
    "GroupSession",
    "Hall",
    "IndividualSession",
    "Membership",
    "MembershipOption",
    "MembershipStatus",
    "Notification",
    "NotificationChannel",
    "NotificationStatus",
    "Payment",
    "PaymentMethod",
    "PaymentStatus",
    "PromoCode",
    "Role",
    "SessionKind",
    "TariffPlan",
    "TariffType",
    "Trainer",
    "TrainingSession",
    "User",
    "Visit",
    "WorkShift",
    "membership_option_links",
]
