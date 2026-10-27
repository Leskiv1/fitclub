"""The three reports required by the assignment (З-1, З-2, З-3)."""

from __future__ import annotations

import calendar
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.clock import Clock
from app.domain.errors import BusinessRuleError
from app.domain.models import (
    BookingStatus,
    Client,
    Hall,
    Membership,
    Payment,
    PaymentStatus,
    TariffPlan,
    TrainingSession,
    Visit,
)
from app.domain.reports.structure import Column, Report, ReportBuilder
from app.services.club_settings import ClubSettingsCache

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
MONTHS = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень", "Серпень",
          "Вересень", "Жовтень", "Листопад", "Грудень"]  # fmt: skip
MAX_PERIOD_DAYS = 366


@dataclass(frozen=True)
class ReportParams:
    """Query parameters; hashable, so the caching proxy can use them as a key."""

    start: date | None = None
    end: date | None = None
    year: int | None = None
    month: int | None = None


@dataclass(frozen=True)
class Period:
    start: date
    end: date  # inclusive
    label: str

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


def _share(part: Decimal | int | float, whole: Decimal | int | float) -> float:
    return round(float(part) / float(whole) * 100, 1) if whole else 0.0


class ReportGenerator(ABC):
    """GoF: Template Method — AbstractClass.

    `generate()` fixes the algorithm: resolve the period → collect data → process it → build the report.
    Subclasses implement `collect` and `build` and may change `resolve_period` and `process`.
    """

    code: str
    title: str

    def __init__(self, session: Session, clock: Clock) -> None:
        self.session = session
        self.clock = clock

    def generate(self, params: ReportParams) -> Report:
        period = self.resolve_period(params)
        data = self.collect(period)
        data = self.process(data, period)
        builder = ReportBuilder(self.code, self.title, self.clock.now()).period(
            period.label, start=period.start, end=period.end
        )
        self.build(builder, data, period)
        return builder.build()

    # --- steps ---

    def resolve_period(self, params: ReportParams) -> Period:
        """Default: an explicit [start, end] or the last 30 days."""
        end = params.end or self.clock.today()
        start = params.start or end - timedelta(days=29)
        return self._checked(start, end)

    @abstractmethod
    def collect(self, period: Period) -> Any: ...

    def process(self, data: Any, period: Period) -> Any:
        return data

    @abstractmethod
    def build(self, builder: ReportBuilder, data: Any, period: Period) -> None: ...

    # --- helpers ---

    @staticmethod
    def _checked(start: date, end: date, label: str | None = None) -> Period:
        if start > end:
            raise BusinessRuleError("Початок періоду має бути не пізніше за кінець")
        if (end - start).days + 1 > MAX_PERIOD_DAYS:
            raise BusinessRuleError(f"Період не може перевищувати {MAX_PERIOD_DAYS} днів")
        return Period(start, end, label or f"{start:%d.%m.%Y} – {end:%d.%m.%Y}")

    def _local_date(self, column):
        """The local date (club time zone) of a timestamptz column, computed in SQL."""
        return cast(func.timezone(self.clock.zone.key, column), Date)

    def _bounds(self, period: Period) -> tuple[datetime, datetime]:
        start = datetime.combine(period.start, time.min, tzinfo=self.clock.zone)
        return start, datetime.combine(period.end + timedelta(days=1), time.min, tzinfo=self.clock.zone)


class ClientActivityReport(ReportGenerator):
    """З-1: all clients with their visit activity. GoF: Template Method — ConcreteClass."""

    code = "client-activity"
    title = "Активність клієнтів"
    ACTIVE_PER_WEEK = 2

    def collect(self, period: Period) -> dict[str, Any]:
        clients = self.session.scalars(
            select(Client)
            .options(selectinload(Client.memberships).selectinload(Membership.tariff_plan))
            .order_by(Client.full_name)
        ).all()
        in_period = (
            select(Membership.client_id, func.count(Visit.id))
            .join(Visit, Visit.membership_id == Membership.id)
            .where(Visit.visit_date.between(period.start, period.end))
            .group_by(Membership.client_id)
        )
        last_visit = (
            select(Membership.client_id, func.max(Visit.visit_date))
            .join(Visit, Visit.membership_id == Membership.id)
            .where(Visit.visit_date <= period.end)
            .group_by(Membership.client_id)
        )
        return {
            "clients": clients,
            "visits": dict(self.session.execute(in_period).all()),
            "last_visit": dict(self.session.execute(last_visit).all()),
        }

    def process(self, data: dict[str, Any], period: Period) -> list[dict[str, Any]]:
        weeks = period.days / 7
        rows = []
        for client in data["clients"]:
            visits = data["visits"].get(client.id, 0)
            per_week = round(visits / weeks, 1)
            membership = client.active_membership(period.end) or (
                client.memberships[-1] if client.memberships else None
            )
            rows.append(
                {
                    "full_name": client.full_name,
                    "phone": client.phone,
                    "tariff": membership.tariff_plan.name if membership else "—",
                    "status": membership.status.value if membership else "—",
                    "valid_until": membership.end_date if membership else None,
                    "visits": visits,
                    "per_week": per_week,
                    "last_visit": data["last_visit"].get(client.id),
                    "activity": (
                        "активний"
                        if per_week >= self.ACTIVE_PER_WEEK
                        else "помірний"
                        if visits
                        else "неактивний"
                    ),
                }
            )
        return sorted(rows, key=lambda row: (-row["visits"], row["full_name"]))

    def build(self, builder: ReportBuilder, rows: list[dict[str, Any]], period: Period) -> None:
        count = {
            level: sum(row["activity"] == level for row in rows)
            for level in ("активний", "помірний", "неактивний")
        }
        total_visits = sum(row["visits"] for row in rows)
        builder.summary(
            "Підсумок",
            [
                ("Клієнтів", len(rows), "int"),
                ("Активних (≥ 2 відвідувань на тиждень)", count["активний"], "int"),
                ("Помірних", count["помірний"], "int"),
                ("Неактивних (без відвідувань)", count["неактивний"], "int"),
                ("Відвідувань за період", total_visits, "int"),
                ("У середньому на клієнта", round(total_visits / len(rows), 1) if rows else 0, "number"),
            ],
        ).table(
            "Клієнти",
            [
                Column("full_name", "ПІБ"),
                Column("phone", "Телефон"),
                Column("tariff", "Абонемент"),
                Column("status", "Статус"),
                Column("valid_until", "Дійсний до", "date"),
                Column("visits", "Відвідувань", "int"),
                Column("per_week", "На тиждень", "number"),
                Column("last_visit", "Останній візит", "date"),
                Column("activity", "Активність"),
            ],
            rows,
        )


class IncomeReport(ReportGenerator):
    """З-2: income of the club for a month or a year. GoF: Template Method — ConcreteClass."""

    code = "income"
    title = "Доходи клубу"

    def resolve_period(self, params: ReportParams) -> Period:
        today = self.clock.today()
        year = params.year or today.year
        if params.month is not None:
            if not 1 <= params.month <= 12:
                raise BusinessRuleError("Місяць — число від 1 до 12")
            last = calendar.monthrange(year, params.month)[1]
            return self._checked(
                date(year, params.month, 1),
                date(year, params.month, last),
                f"{MONTHS[params.month - 1]} {year}",
            )
        if params.year is None:  # nothing given: the current month
            return self.resolve_period(ReportParams(year=today.year, month=today.month))
        return self._checked(date(year, 1, 1), date(year, 12, 31), f"{year} рік")

    def collect(self, period: Period) -> dict[str, Any]:
        paid_on = self._local_date(Payment.paid_at)
        paid = (
            Payment.status == PaymentStatus.PAID,
            paid_on.between(period.start, period.end),
        )
        by_tariff = self.session.execute(
            select(
                TariffPlan.name,
                func.count(Payment.id),
                func.sum(Payment.amount),
                func.sum(Membership.discount_amount),
            )
            .join(Membership, Payment.membership_id == Membership.id)
            .join(TariffPlan, Membership.tariff_plan_id == TariffPlan.id)
            .where(*paid)
            .group_by(TariffPlan.name)
            .order_by(func.sum(Payment.amount).desc())
        ).all()
        by_day = self.session.execute(
            select(paid_on, func.count(Payment.id), func.sum(Payment.amount)).where(*paid).group_by(paid_on)
        ).all()
        return {"by_tariff": by_tariff, "by_day": by_day}

    def process(self, data: dict[str, Any], period: Period) -> dict[str, Any]:
        yearly = period.days > 31
        buckets: dict[Any, list] = {}
        if yearly:
            for month in range(1, 13):
                buckets[month] = [MONTHS[month - 1], 0, Decimal("0")]
        else:
            for offset in range(period.days):
                day = period.start + timedelta(days=offset)
                buckets[day] = [day, 0, Decimal("0")]
        for day, count, amount in data["by_day"]:
            bucket = buckets[day.month if yearly else day]
            bucket[1] += count
            bucket[2] += amount
        revenue = sum((row[2] for row in data["by_tariff"]), Decimal("0"))
        return {
            "yearly": yearly,
            "revenue": revenue,
            "payments": sum(row[1] for row in data["by_tariff"]),
            "discounts": sum((row[3] or Decimal("0") for row in data["by_tariff"]), Decimal("0")),
            "by_tariff": [
                {"tariff": name, "sold": count, "revenue": amount, "share": _share(amount, revenue)}
                for name, count, amount, _ in data["by_tariff"]
            ],
            "by_time": [
                {"period": label, "payments": count, "revenue": amount}
                for label, count, amount in buckets.values()
            ],
        }

    def build(self, builder: ReportBuilder, data: dict[str, Any], period: Period) -> None:
        average = (
            (data["revenue"] / data["payments"]).quantize(Decimal("0.01"))
            if data["payments"]
            else Decimal("0")
        )
        builder.summary(
            "Підсумок",
            [
                ("Виручка", data["revenue"], "money"),
                ("Кількість оплат", data["payments"], "int"),
                ("Середній чек", average, "money"),
                ("Надано знижок", data["discounts"], "money"),
            ],
        ).table(
            "За тарифами",
            [
                Column("tariff", "Тариф"),
                Column("sold", "Продано", "int"),
                Column("revenue", "Виручка", "money"),
                Column("share", "Частка, %", "percent"),
            ],
            data["by_tariff"],
            totals={
                "tariff": "Разом",
                "sold": data["payments"],
                "revenue": data["revenue"],
                "share": 100.0 if data["payments"] else 0.0,
            },
        ).table(
            "За місяцями" if data["yearly"] else "За днями",
            [
                Column(
                    "period", "Місяць" if data["yearly"] else "Дата", "text" if data["yearly"] else "date"
                ),
                Column("payments", "Оплат", "int"),
                Column("revenue", "Виручка", "money"),
            ],
            data["by_time"],
            totals={"period": "Разом", "payments": data["payments"], "revenue": data["revenue"]},
        )


class LoadReport(ReportGenerator):
    """З-3: load of trainers and halls by day of the week. GoF: Template Method — ConcreteClass."""

    code = "load"
    title = "Завантаженість тренерів і залів"

    def resolve_period(self, params: ReportParams) -> Period:
        if params.start or params.end:
            return super().resolve_period(params)
        monday = self.clock.today() - timedelta(days=self.clock.today().weekday())
        return self._checked(monday, monday + timedelta(days=6))

    def collect(self, period: Period) -> dict[str, Any]:
        start, end = self._bounds(period)
        sessions = self.session.scalars(
            select(TrainingSession)
            .where(
                TrainingSession.start_at >= start,
                TrainingSession.start_at < end,
                TrainingSession.is_cancelled.is_(False),
            )
            .options(
                selectinload(TrainingSession.trainer),
                selectinload(TrainingSession.hall),
                selectinload(TrainingSession.bookings),
            )
        ).all()
        halls = self.session.scalars(select(Hall).order_by(Hall.name)).all()
        return {"sessions": sessions, "halls": halls, "settings": ClubSettingsCache().get(self.session)}

    def process(self, data: dict[str, Any], period: Period) -> dict[str, Any]:
        trainers: dict[int, dict[str, Any]] = {}
        hall_hours: dict[int, list[float]] = defaultdict(lambda: [0.0] * 7)
        for training in data["sessions"]:
            weekday = training.start_at.astimezone(self.clock.zone).weekday()
            hours = (training.end_at - training.start_at).total_seconds() / 3600
            booked = sum(b.status != BookingStatus.CANCELLED for b in training.bookings)
            empty = {
                "trainer": training.trainer.full_name,
                "sessions": 0,
                "hours": 0.0,
                "bookings": 0,
                "_fill": [],
            }
            row = trainers.setdefault(training.trainer_id, empty | {f"d{d}": 0.0 for d in range(7)})
            row["sessions"] += 1
            row["hours"] += hours
            row["bookings"] += booked
            row["_fill"].append(_share(booked, training.capacity()))
            row[f"d{weekday}"] += hours
            hall_hours[training.hall_id][weekday] += hours

        trainer_rows = []
        for row in sorted(trainers.values(), key=lambda r: -r["hours"]):
            fills = row.pop("_fill")
            row["fill"] = round(sum(fills) / len(fills), 1)
            row["hours"] = round(row["hours"], 1)
            trainer_rows.append(row | {f"d{d}": round(row[f"d{d}"], 1) for d in range(7)})

        open_hours = self._open_hours_per_weekday(data["settings"].opening_hours, period)
        hall_rows = []
        for hall in data["halls"]:
            used = hall_hours[hall.id]
            row = {
                "hall": hall.name,
                "hours": round(sum(used), 1),
                "total": _share(sum(used), sum(open_hours)),
            }
            row |= {f"d{d}": _share(used[d], open_hours[d]) for d in range(7)}
            hall_rows.append(row)
        return {"trainers": trainer_rows, "halls": hall_rows}

    def build(self, builder: ReportBuilder, data: dict[str, Any], period: Period) -> None:
        days_hours = [Column(f"d{d}", f"{name}, год", "number") for d, name in enumerate(WEEKDAYS)]
        days_percent = [Column(f"d{d}", f"{name}, %", "percent") for d, name in enumerate(WEEKDAYS)]
        builder.group("Тренери").table(
            "Заняття і години по днях тижня",
            [
                Column("trainer", "Тренер"),
                Column("sessions", "Занять", "int"),
                Column("hours", "Годин", "number"),
                Column("bookings", "Записів", "int"),
                Column("fill", "Заповненість, %", "percent"),
                *days_hours,
            ],
            data["trainers"],
        ).end_group().group("Зали").table(
            "Зайнятість від годин роботи клубу",
            [
                Column("hall", "Зал"),
                Column("hours", "Годин", "number"),
                Column("total", "Загалом, %", "percent"),
                *days_percent,
            ],
            data["halls"],
        ).end_group()

    @staticmethod
    def _open_hours_per_weekday(opening_hours: dict[str, list[str]], period: Period) -> list[float]:
        """How many hours the club is open on each weekday within the period."""
        totals = [0.0] * 7
        for offset in range(period.days):
            day = period.start + timedelta(days=offset)
            hours = opening_hours.get(str(day.weekday()))
            if hours:
                opens, closes = (time.fromisoformat(h) for h in hours)
                totals[day.weekday()] += (
                    datetime.combine(day, closes) - datetime.combine(day, opens)
                ).total_seconds() / 3600
        return totals


GENERATORS: dict[str, type[ReportGenerator]] = {
    generator.code: generator for generator in (ClientActivityReport, IncomeReport, LoadReport)
}
