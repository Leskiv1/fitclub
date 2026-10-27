"""Domain events and the event bus (GoF Observer)."""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger("fitclub.events")


@dataclass(frozen=True)
class DomainEvent:
    """Something that has happened in the domain; carries ids, not ORM objects (they belong to a session)."""


@dataclass(frozen=True)
class MembershipPurchased(DomainEvent):
    membership_id: int


@dataclass(frozen=True)
class MembershipExpiringSoon(DomainEvent):
    membership_id: int
    days_left: int


@dataclass(frozen=True)
class VisitRegistered(DomainEvent):
    visit_id: int
    membership_id: int


class EventObserver(ABC):
    """GoF: Observer — Observer."""

    @abstractmethod
    def notify(self, event: DomainEvent) -> None: ...


class EventBus:
    """GoF: Observer — Subject. Publishers do not know who reacts to their events.

    Events must be published after the transaction is committed, so nobody reacts to changes that were
    rolled back. A failing observer is logged and does not stop the others.
    """

    def __init__(self) -> None:
        self._observers: dict[type[DomainEvent], list[EventObserver]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], observer: EventObserver) -> None:
        self._observers[event_type].append(observer)

    def publish(self, event: DomainEvent) -> None:
        for observer in self._observers[type(event)]:
            try:
                observer.notify(event)
            except Exception:
                logger.exception("Observer %s failed on %s", type(observer).__name__, event)
