"""Local demo data for development and screenshots (not committed).

Run from the project root:  backend/.venv/Scripts/python seed/seed_demo.py
Clears all tables except club_settings and fills them again; dates are relative to today.
"""

import logging
import random
import sys
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import text  # noqa: E402

from app.core.clock import Clock  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.database import Base, SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.domain.membership.factories import factory_for  # noqa: E402
from app.domain.membership.pricing import build_price  # noqa: E402
from app.domain.models import (  # noqa: E402
    Booking,
    BookingStatus,
    Client,
    ClubSettings,
    GroupSession,
    Hall,
    IndividualSession,
    Membership,
    MembershipOption,
    MembershipStatus,
    NotificationChannel,
    Payment,
    PaymentMethod,
    PromoCode,
    Role,
    TariffPlan,
    TariffType,
    Trainer,
    User,
    Visit,
    WorkShift,
)
from app.services.notifications.daily_check import ExpiringMembershipsJob  # noqa: E402
from app.services.notifications.observers import build_event_bus  # noqa: E402

rng = random.Random(42)
CLUB_ZONE = ZoneInfo(get_settings().club_timezone)
TODAY = datetime.now(CLUB_ZONE).date()

FIRST_NAMES_M = [
    "Олександр",
    "Андрій",
    "Дмитро",
    "Максим",
    "Іван",
    "Тарас",
    "Богдан",
    "Назар",
    "Юрій",
    "Олег",
]
FIRST_NAMES_F = [
    "Олена",
    "Марія",
    "Анна",
    "Ірина",
    "Софія",
    "Катерина",
    "Юлія",
    "Наталія",
    "Дарина",
    "Вікторія",
]
LAST_NAMES = [
    ("Шевченко", "Шевченко"),
    ("Коваленко", "Коваленко"),
    ("Бондаренко", "Бондаренко"),
    ("Ткаченко", "Ткаченко"),
    ("Кравчук", "Кравчук"),
    ("Мельник", "Мельник"),
    ("Олійник", "Олійник"),
    ("Савчук", "Савчук"),
    ("Лисенко", "Лисенко"),
    ("Мороз", "Мороз"),
    ("Гнатюк", "Гнатюк"),
    ("Петрів", "Петрів"),
    ("Романюк", "Романюк"),
    ("Левицький", "Левицька"),
    ("Захарчук", "Захарчук"),
]


def local(day: date, at: time) -> datetime:
    """Aware datetime in the machine's local time zone."""
    return datetime.combine(day, at, tzinfo=CLUB_ZONE)


def clear(session) -> None:
    tables = [t.name for t in Base.metadata.sorted_tables if t.name != "club_settings"]
    session.execute(text(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE"))


def user(email: str, role: Role, password: str) -> User:
    return User(email=email, password_hash=hash_password(password), role=role)


def seed_staff(session) -> list[Trainer]:
    session.add_all(
        [
            user("admin@fitclub.example", Role.ADMIN, "admin123"),
            user("reception@fitclub.example", Role.RECEPTION, "reception123"),
        ]
    )
    weekdays_morning = [(d, time(7, 0), time(15, 0)) for d in range(5)]
    weekdays_evening = [(d, time(14, 0), time(22, 0)) for d in range(5)]
    weekend = [(d, time(9, 0), time(17, 0)) for d in (5, 6)]
    profiles = [
        ("Ірина Мельник", "Йога, пілатес, стретчинг", weekdays_morning + weekend[:1]),
        ("Андрій Коваль", "Кросфіт, функціональний тренінг", weekdays_evening),
        ("Олег Бойко", "Силові тренування, бодібілдинг", weekdays_morning),
        ("Дарина Литвин", "Аеробіка, зумба, танцювальний фітнес", weekdays_evening + weekend),
    ]
    trainers = []
    for n, (name, specialization, shifts) in enumerate(profiles, start=1):
        trainer = Trainer(
            user=user(f"trainer{n}@fitclub.example", Role.TRAINER, "trainer123"),
            full_name=name,
            specialization=specialization,
            bio=f"Досвід роботи понад {rng.randint(3, 12)} років.",
            work_shifts=[WorkShift(weekday=d, start_time=s, end_time=e) for d, s, e in shifts],
        )
        trainers.append(trainer)
    session.add_all(trainers)
    return trainers


def seed_catalog(session) -> tuple[list[Hall], dict[str, TariffPlan], list[MembershipOption]]:
    halls = [
        Hall(name="Тренажерний зал", capacity=40),
        Hall(name="Зал групових програм", capacity=25),
        Hall(name="Студія йоги", capacity=15),
    ]
    tariffs = {
        "single": TariffPlan(
            name="Разове відвідування",
            type=TariffType.SINGLE_VISIT,
            price=Decimal("200"),
            duration_days=1,
            visit_limit=1,
            description="Одне відвідування тренажерного залу",
        ),
        "pack": TariffPlan(
            name="Пакет 8 відвідувань",
            type=TariffType.VISIT_PACK,
            price=Decimal("1200"),
            duration_days=60,
            visit_limit=8,
            description="8 відвідувань протягом 60 днів",
        ),
        "monthly12": TariffPlan(
            name="Місячний 12 відвідувань",
            type=TariffType.MONTHLY,
            price=Decimal("850"),
            duration_days=30,
            visit_limit=12,
            description="12 відвідувань, групові заняття включено",
        ),
        "monthly": TariffPlan(
            name="Місячний безліміт",
            type=TariffType.MONTHLY,
            price=Decimal("1100"),
            duration_days=30,
            visit_limit=None,
            description="Безлімітні відвідування та групові заняття",
        ),
        "yearly": TariffPlan(
            name="Річний безліміт",
            type=TariffType.YEARLY,
            price=Decimal("9900"),
            duration_days=365,
            visit_limit=None,
            description="Безліміт на рік, 2 тижні заморозки",
        ),
    }
    options = [
        MembershipOption(name="Сауна", price=Decimal("300")),
        MembershipOption(name="Шафка", price=Decimal("150")),
        MembershipOption(name="Рушник", price=Decimal("100")),
        MembershipOption(name="Персональне тренування", price=Decimal("450")),
    ]
    session.add_all([*halls, *tariffs.values(), *options])
    session.add_all(
        [
            PromoCode(code="WELCOME10", percent=10),
            PromoCode(code="AUTUMN20", percent=20, valid_until=TODAY + timedelta(days=30)),
            PromoCode(code="SUMMER15", percent=15, valid_until=TODAY - timedelta(days=40)),
        ]
    )
    return halls, tariffs, options


def seed_clients(session, count: int = 25) -> list[Client]:
    clients = []
    for n in range(1, count + 1):
        female = n % 2 == 0
        first = rng.choice(FIRST_NAMES_F if female else FIRST_NAMES_M)
        last_m, last_f = rng.choice(LAST_NAMES)
        birth = TODAY - timedelta(days=rng.randint(18 * 365, 60 * 365))
        clients.append(
            Client(
                user=user(f"client{n}@fitclub.example", Role.CLIENT, "client123"),
                full_name=f"{last_f if female else last_m} {first}",
                birth_date=birth,
                phone=f"+38067{1000000 + n * 7919 % 9000000:07d}",
                notification_channel=rng.choice(list(NotificationChannel)),
                created_at=local(TODAY - timedelta(days=rng.randint(60, 400)), time(12, 0)),
            )
        )
    session.add_all(clients)
    return clients


def buy(client, tariff, start: date, status: MembershipStatus, options=()) -> Membership:
    """Same rules as the application: dates from the tariff's factory, price from option decorators."""
    membership = factory_for(tariff.type).issue(client, tariff, start, options)
    membership.total_price = build_price(tariff, options).price()
    membership.discount_amount = Decimal("0")
    membership.status = status
    if status == MembershipStatus.FROZEN:
        membership.frozen_at = TODAY - timedelta(days=10)
    if status != MembershipStatus.PENDING:
        membership.payment = Payment(
            amount=membership.total_price,
            method=rng.choice(list(PaymentMethod)),
            paid_at=local(start, time(rng.randint(8, 20), rng.choice([0, 15, 30, 45]))),
        )
    return membership


def add_visits(membership: Membership, settings: ClubSettings, per_week: float) -> None:
    last_day = min(membership.end_date, TODAY)
    day = membership.start_date
    while day <= last_day:
        if membership.visits_left == 0:
            break
        hours = settings.opening_hours.get(str(day.weekday()))
        if hours and rng.random() < per_week / 7:
            opens, closes = (time.fromisoformat(h) for h in hours)
            hour = rng.randint(opens.hour, closes.hour - 2)
            checked_in = local(day, time(hour, rng.randint(0, 59)))
            if day == TODAY and checked_in > datetime.now(CLUB_ZONE):
                break
            membership.visits.append(Visit(checked_in_at=checked_in, visit_date=day))
            if membership.visits_left is not None:
                membership.visits_left -= 1
        day += timedelta(days=1)


def seed_memberships(session, clients, tariffs, options, settings) -> None:
    for n, client in enumerate(clients):
        activity = rng.choice([0.5, 1.5, 2.5, 3.5, 5.0])  # visits per week → З-1 activity report
        # previous membership (expired), bought ~2–3 months ago
        if n % 3 != 0:
            past_tariff = rng.choice([tariffs["monthly"], tariffs["monthly12"], tariffs["pack"]])
            past_start = TODAY - timedelta(days=rng.randint(70, 95))
            past = buy(client, past_tariff, past_start, MembershipStatus.EXPIRED)
            past.end_date = min(past.end_date, TODAY - timedelta(days=1))
            add_visits(past, settings, activity)
            session.add(past)

        # current membership, with a scenario per client
        scenario = n % 10
        chosen = rng.sample(options, k=rng.choice([0, 0, 1, 2]))
        if scenario in (0, 1):  # expiring within the warning period → Ф-6
            tariff = tariffs["monthly"]
            start = TODAY - timedelta(days=tariff.duration_days - 1 - rng.randint(0, 3))
            status = MembershipStatus.ACTIVE
        elif scenario == 2:  # expired recently, did not renew
            tariff = tariffs["monthly12"]
            start = TODAY - timedelta(days=40)
            status = MembershipStatus.EXPIRED
        elif scenario == 3 and n == 3:
            tariff, start, status = tariffs["yearly"], TODAY - timedelta(days=120), MembershipStatus.FROZEN
        elif scenario == 4 and n == 4:
            tariff, start, status = tariffs["monthly"], TODAY, MembershipStatus.PENDING
        elif scenario == 5:
            tariff, start, status = (
                tariffs["yearly"],
                TODAY - timedelta(days=rng.randint(30, 200)),
                MembershipStatus.ACTIVE,
            )
        else:
            tariff = rng.choice([tariffs["monthly"], tariffs["monthly12"], tariffs["pack"]])
            start = TODAY - timedelta(days=rng.randint(0, tariff.duration_days - 5))
            status = MembershipStatus.ACTIVE

        current = buy(client, tariff, start, status, chosen)
        if status in (MembershipStatus.ACTIVE, MembershipStatus.EXPIRED):
            add_visits(current, settings, activity)
        if status == MembershipStatus.FROZEN:
            add_visits(current, settings, activity)
            current.visits = [
                v for v in current.visits if v.checked_in_at.date() < TODAY - timedelta(days=10)
            ]
        session.add(current)

    # one single-visit guest purchase today
    session.add(buy(clients[-1], tariffs["single"], TODAY, MembershipStatus.ACTIVE))


GROUP_TEMPLATE = [
    # weekday, start, minutes, title, trainer index, hall index, places
    (0, time(8, 0), 60, "Ранкова йога", 0, 2, 15),
    (0, time(19, 0), 60, "Кросфіт", 1, 1, 20),
    (1, time(9, 0), 55, "Пілатес", 0, 2, 12),
    (1, time(18, 30), 60, "Зумба", 3, 1, 25),
    (2, time(8, 0), 60, "Ранкова йога", 0, 2, 15),
    (2, time(19, 0), 60, "Функціональний тренінг", 1, 1, 20),
    (3, time(10, 0), 60, "Силова витривалість", 2, 0, 12),
    (3, time(18, 30), 60, "Зумба", 3, 1, 25),
    (4, time(19, 0), 60, "Кросфіт", 1, 1, 20),
    (5, time(10, 0), 75, "Стретчинг", 0, 2, 15),
    (6, time(11, 0), 60, "Танцювальний фітнес", 3, 1, 25),
]


def members_on(clients, day: date) -> list[Client]:
    """Clients whose membership covered that day (active then, frozen memberships excluded)."""
    usable = (MembershipStatus.ACTIVE, MembershipStatus.EXPIRED)
    return [
        client
        for client in clients
        if any(m.status in usable and m.start_date <= day <= m.end_date for m in client.memberships)
    ]


def seed_sessions(session, trainers, halls, clients) -> None:
    week_start = TODAY - timedelta(days=TODAY.weekday())
    now = datetime.now(CLUB_ZONE)
    for week in range(-4, 2):  # 4 past weeks for З-3, current and next week for booking
        for weekday, start_time, minutes, title, t_idx, h_idx, places in GROUP_TEMPLATE:
            day = week_start + timedelta(weeks=week, days=weekday)
            start = local(day, start_time)
            group = GroupSession(
                trainer=trainers[t_idx],
                hall=halls[h_idx],
                title=title,
                max_participants=places,
                start_at=start,
                end_at=start + timedelta(minutes=minutes),
            )
            past = start < now
            fill = rng.uniform(0.4, 1.0) if past else rng.uniform(0.1, 0.7)
            members = members_on(clients, day)
            for client in rng.sample(members, k=min(len(members), int(places * fill))):
                status = BookingStatus.ATTENDED if past else BookingStatus.BOOKED
                if rng.random() < 0.08:
                    status = BookingStatus.CANCELLED
                group.bookings.append(Booking(client=client, status=status))
            session.add(group)

        # a few individual sessions inside the trainers' shifts
        for _ in range(6):
            trainer = rng.choice(trainers)
            shift = rng.choice(trainer.work_shifts)
            day = week_start + timedelta(weeks=week, days=shift.weekday)
            hour = rng.randint(shift.start_time.hour, shift.end_time.hour - 1)
            start = local(day, time(hour, 0))
            members = members_on(clients, day)
            end = start + timedelta(hours=1)
            if not members or not trainer.is_available(start, end) or not halls[0].is_free(start, end):
                continue
            individual = IndividualSession(
                trainer=trainer, hall=halls[0], start_at=start, end_at=start + timedelta(hours=1)
            )
            status = BookingStatus.ATTENDED if start < now else BookingStatus.BOOKED
            individual.bookings.append(Booking(client=rng.choice(members), status=status))
            session.add(individual)


def seed_notifications(session) -> None:
    """Reminders are produced by the real daily job: Observer -> channel factory -> adapter."""
    logging.getLogger("fitclub.notifications").setLevel(logging.WARNING)  # the fake e-mails are long
    clock = Clock()
    ExpiringMembershipsJob(session, clock, build_event_bus(session, clock)).run()


def main() -> None:
    with SessionLocal() as session:
        clear(session)
        settings = session.get(ClubSettings, 1)
        trainers = seed_staff(session)
        halls, tariffs, options = seed_catalog(session)
        clients = seed_clients(session)
        session.flush()
        seed_memberships(session, clients, tariffs, options, settings)
        seed_sessions(session, trainers, halls, clients)
        session.flush()
        session.commit()
        seed_notifications(session)
        session.commit()

        counts = {
            table.name: session.execute(text(f"SELECT count(*) FROM {table.name}")).scalar()
            for table in Base.metadata.sorted_tables
        }
    for name, value in counts.items():
        print(f"{name:25} {value}")
    print("\nЛогіни: admin@fitclub.example / admin123, reception@fitclub.example / reception123,")
    print("        trainer1..4@fitclub.example / trainer123, client1..25@fitclub.example / client123")


if __name__ == "__main__":
    main()
