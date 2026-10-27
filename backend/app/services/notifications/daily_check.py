"""Daily job (Ф-6): expire overdue memberships and remind clients whose membership ends soon."""

import logging
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.database import SessionLocal
from app.domain.events import EventBus, MembershipExpiringSoon
from app.repositories.memberships import MembershipRepository
from app.services.club_settings import ClubSettingsCache
from app.services.notifications.observers import build_event_bus

logger = logging.getLogger("fitclub.scheduler")

# any constant shared by all processes: only one of them may run the job at a time
DAILY_CHECK_LOCK_KEY = 2026_06_00


@dataclass(frozen=True)
class DailyCheckResult:
    expired: int = 0
    reminders: int = 0
    skipped: bool = False  # another process holds the lock


class ExpiringMembershipsJob:
    def __init__(self, session: Session, clock: Clock, events: EventBus) -> None:
        self.session = session
        self.clock = clock
        self.events = events
        self.memberships = MembershipRepository(session)

    def run(self) -> DailyCheckResult:
        # transaction-level advisory lock: with several uvicorn workers only one runs the check
        locked = self.session.scalar(select(func.pg_try_advisory_xact_lock(DAILY_CHECK_LOCK_KEY)))
        if not locked:
            return DailyCheckResult(skipped=True)

        settings = ClubSettingsCache().get(self.session)
        today = self.clock.today()

        overdue = self.memberships.overdue(today)
        for membership in overdue:
            membership.expire()  # GoF State: Active → Expired

        candidates = self.memberships.reminder_candidates(
            today, today + timedelta(days=settings.expiry_warning_days)
        )
        reminders = [(m.id, m.days_left(today)) for m in candidates]
        self.session.commit()  # also releases the lock

        # events go out only after the commit, so observers see the final data
        if settings.notifications_enabled:
            for membership_id, days_left in reminders:
                self.events.publish(MembershipExpiringSoon(membership_id=membership_id, days_left=days_left))
        return DailyCheckResult(
            expired=len(overdue), reminders=len(reminders) if settings.notifications_enabled else 0
        )


def run_daily_check() -> DailyCheckResult:
    """Entry point for the scheduler: a fresh DB session outside any HTTP request."""
    clock = Clock()
    with SessionLocal() as session:
        result = ExpiringMembershipsJob(session, clock, build_event_bus(session, clock)).run()
    logger.info("Daily membership check: %s", result)
    return result
