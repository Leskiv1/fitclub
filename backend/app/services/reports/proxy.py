"""Caching proxy in front of report generators."""

import time as monotonic_time
from threading import Lock

from app.core.clock import Clock
from app.domain.reports.structure import Report
from app.services.reports.generators import ReportGenerator, ReportParams

CLOSED_PERIOD_TTL = 3600.0  # a past month or year will not change any more
OPEN_PERIOD_TTL = 60.0  # the current period gets new payments and visits


class ReportCache:
    """Process-wide storage of generated reports (one instance per process, like the settings cache)."""

    def __init__(self) -> None:
        self._items: dict[tuple, tuple[float, Report]] = {}
        self._lock = Lock()

    def get(self, key: tuple) -> Report | None:
        with self._lock:
            item = self._items.get(key)
            if item is None or item[0] < monotonic_time.monotonic():
                self._items.pop(key, None)
                return None
            return item[1]

    def put(self, key: tuple, report: Report, ttl: float) -> None:
        with self._lock:
            self._items[key] = (monotonic_time.monotonic() + ttl, report)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


report_cache = ReportCache()


class CachingReportProxy:
    """GoF: Proxy — has the same `generate(params)` interface as a generator and caches its reports.

    The real generator (RealSubject) runs only when the report is not cached or the cache entry has expired;
    reports for closed periods are kept longer than those for the current period.
    """

    def __init__(self, generator: ReportGenerator, clock: Clock, cache: ReportCache = report_cache) -> None:
        self.generator = generator
        self.clock = clock
        self.cache = cache

    def generate(self, params: ReportParams) -> Report:
        period = self.generator.resolve_period(params)  # also validates the parameters
        key = (self.generator.code, period.start, period.end)
        report = self.cache.get(key)
        if report is None:
            report = self.generator.generate(params)
            ttl = CLOSED_PERIOD_TTL if period.end < self.clock.today() else OPEN_PERIOD_TTL
            self.cache.put(key, report, ttl)
        return report
