"""Registering a client's arrival at the club (Ф-2)."""

from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.domain.checkin.chain import CheckInContext, CheckInDeniedError, build_check_in_chain
from app.domain.errors import NotFoundError
from app.domain.events import EventBus, VisitRegistered
from app.domain.models import Visit
from app.repositories.clients import ClientRepository
from app.repositories.memberships import MembershipRepository
from app.repositories.visits import VisitRepository
from app.services.club_settings import ClubSettingsCache


class CheckInFacade:
    """GoF: Facade — one call for the reception: load data → run the entry checks → register the visit.

    Subsystems: repositories, the Chain of Responsibility of entry checks, the membership State (check_in).
    """

    def __init__(self, session: Session, clock: Clock | None = None, events: EventBus | None = None) -> None:
        self.session = session
        self.clock = clock or Clock()
        self.clients = ClientRepository(session)
        self.memberships = MembershipRepository(session)
        self.visits = VisitRepository(session)
        self.events = events or EventBus()
        self.chain = build_check_in_chain()

    def check_in(self, client_id: int) -> Visit:
        client = self.clients.get(client_id)
        if client is None:
            raise NotFoundError("Клієнт", client_id)

        now = self.clock.now()
        context = CheckInContext(
            client=client,
            # locked until commit: a parallel check-in of the same client waits here
            memberships=list(self.memberships.covering(client.id, now.date(), lock=True)),
            settings=ClubSettingsCache().get(self.session),  # GoF Singleton
            now=now,
            visit_today=self.visits.client_visit_on(client.id, now.date()),
        )
        self.chain.handle(context)  # raises CheckInDeniedError with the first reason found

        visit = context.membership.check_in(now)  # State: counts the visit, may expire a visit pack
        try:
            # explicit add: SQLAlchemy 2 does not cascade a new object into the session via a backref
            self.visits.add(visit)
        except IntegrityError as exc:  # the unique (membership, day) index caught a race the lock missed
            self.session.rollback()
            raise CheckInDeniedError("already_checked_in", "Клієнта вже відмічено сьогодні") from exc
        self.session.commit()
        self.events.publish(VisitRegistered(visit_id=visit.id, membership_id=visit.membership_id))
        return visit

    def visits_today(self) -> Sequence[Visit]:
        return self.visits.on_day(self.clock.today())

    def history(self, client_id: int, *, offset: int, limit: int) -> tuple[Sequence[Visit], int]:
        if self.clients.get(client_id) is None:
            raise NotFoundError("Клієнт", client_id)
        return self.visits.for_client_page(client_id, offset=offset, limit=limit)
