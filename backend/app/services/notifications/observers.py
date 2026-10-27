"""Observers that react to domain events."""

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.domain.events import (
    DomainEvent,
    EventBus,
    EventObserver,
    MembershipExpiringSoon,
    MembershipPurchased,
    VisitRegistered,
)
from app.domain.models import Membership, Notification, NotificationKind, NotificationStatus
from app.services.club_settings import ClubSettingsCache
from app.services.notifications.channels import NotificationContent, channel_factory
from app.services.notifications.senders import DeliveryError

logger = logging.getLogger("fitclub.events")

VISITS_LOW_THRESHOLD = 2


class NotificationObserver(EventObserver):
    """GoF: Observer — ConcreteObserver: turns events into notifications sent over the client's channel."""

    def __init__(self, session: Session, clock: Clock) -> None:
        self.session = session
        self.clock = clock

    def notify(self, event: DomainEvent) -> None:
        try:
            if not ClubSettingsCache().get(self.session).notifications_enabled:
                return
            membership = self.session.get(Membership, event.membership_id)
            content = self._content(event, membership)
            if content is not None:
                self._send(membership, content)
        except Exception:
            # The publisher has already committed; undo only this observer's unfinished work so the
            # shared session stays usable for the rest of the request.
            self.session.rollback()
            raise

    def _content(self, event: DomainEvent, membership: Membership) -> NotificationContent | None:
        common = {
            "client_name": membership.client.full_name,
            "tariff_name": membership.tariff_plan.name,
            "start_date": membership.start_date,
            "end_date": membership.end_date,
        }
        match event:
            case MembershipPurchased():
                return NotificationContent(kind=NotificationKind.MEMBERSHIP_PURCHASED, **common)
            case MembershipExpiringSoon(days_left=days_left):
                return NotificationContent(
                    kind=NotificationKind.MEMBERSHIP_EXPIRING, days_left=days_left, **common
                )
            case VisitRegistered() if membership.visits_left == VISITS_LOW_THRESHOLD:
                return NotificationContent(
                    kind=NotificationKind.VISITS_LOW, visits_left=membership.visits_left, **common
                )
        return None

    def _send(self, membership: Membership, content: NotificationContent) -> None:
        if self._already_sent(membership.id, content.kind):
            return
        client = membership.client
        factory = channel_factory(client.notification_channel)  # GoF Abstract Factory
        message = factory.create_formatter().format(content)
        try:
            # the unique index stops a duplicate from a parallel worker
            with self.session.begin_nested():
                # created inside the savepoint and added at once: SQLAlchemy 2 does not cascade a new
                # object into the session through the client/membership back-references
                notification = Notification(
                    client=client,
                    membership=membership,
                    kind=content.kind,
                    channel=factory.channel,
                    subject=message.subject,
                    message=message.body,
                    status=NotificationStatus.PENDING,
                )
                self.session.add(notification)
        except IntegrityError:
            return

        try:
            factory.create_sender().send(factory.recipient(client), message)
        except DeliveryError as exc:
            notification.status = NotificationStatus.FAILED
            notification.error = str(exc)[:300]
            logger.warning("Notification %s failed: %s", notification.id, exc)
        else:
            notification.status = NotificationStatus.SENT
            notification.sent_at = self.clock.now()
        self.session.commit()

    def _already_sent(self, membership_id: int, kind: NotificationKind) -> bool:
        query = select(Notification.id).where(
            Notification.membership_id == membership_id, Notification.kind == kind
        )
        return self.session.scalar(query) is not None


class AuditLogObserver(EventObserver):
    """GoF: Observer — ConcreteObserver: writes every domain event to the application log."""

    def notify(self, event: DomainEvent) -> None:
        logger.info("Event: %s", event)


def build_event_bus(session: Session, clock: Clock) -> EventBus:
    """Wires observers to the events they are interested in."""
    bus = EventBus()
    notifications = NotificationObserver(session, clock)
    audit = AuditLogObserver()
    for event_type in (MembershipPurchased, MembershipExpiringSoon, VisitRegistered):
        bus.subscribe(event_type, notifications)
        bus.subscribe(event_type, audit)
    return bus
