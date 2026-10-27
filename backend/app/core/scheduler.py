"""Background scheduler for the daily membership check (APScheduler)."""

import logging
from collections.abc import Callable
from datetime import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings

logger = logging.getLogger("fitclub.scheduler")


class DailyJobScheduler:
    """Runs one job every day at a given local time of the club; the time can be changed at run time."""

    JOB_ID = "daily-membership-check"
    SYNC_JOB_ID = "sync-check-time"

    def __init__(self, timezone: str) -> None:
        self.timezone = timezone
        self._scheduler = BackgroundScheduler(timezone=timezone)
        self._at: time | None = None

    @property
    def running(self) -> bool:
        return self._scheduler.running

    def start(
        self, at: time, job: Callable[[], object], check_time: Callable[[], time] | None = None
    ) -> None:
        """`check_time` returns the currently configured time; it is polled every minute because a
        settings change reaches only the worker that handled the request (each worker has its own scheduler).
        """
        self._at = at
        self._scheduler.add_job(
            job,
            self._trigger(at),
            id=self.JOB_ID,
            replace_existing=True,
            coalesce=True,  # after downtime run once, not once per missed day
            misfire_grace_time=3600,
        )
        if check_time is not None:
            self._scheduler.add_job(
                lambda: self.reschedule(check_time()),
                "interval",
                minutes=1,
                id=self.SYNC_JOB_ID,
                replace_existing=True,
            )
        self._scheduler.start()
        logger.info("Daily membership check scheduled at %s (%s)", at, self.timezone)

    def reschedule(self, at: time) -> None:
        if self.running and at != self._at:
            self._scheduler.reschedule_job(self.JOB_ID, trigger=self._trigger(at))
            self._at = at
            logger.info("Daily membership check moved to %s", at)

    def shutdown(self) -> None:
        if self.running:
            self._scheduler.shutdown(wait=False)

    def _trigger(self, at: time) -> CronTrigger:
        return CronTrigger(hour=at.hour, minute=at.minute, timezone=self.timezone)


# One scheduler per process. A plain module-level object is the idiomatic Python way to share it;
# compare with ClubSettingsCache, where the Singleton is enforced by a metaclass.
scheduler = DailyJobScheduler(get_settings().club_timezone)
