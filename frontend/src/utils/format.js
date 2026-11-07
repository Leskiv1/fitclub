import { dayjs, ISO_DATE } from './dates';

// Display helpers and Ukrainian labels for the enums of the API

const money = new Intl.NumberFormat('uk-UA', {
  style: 'currency',
  currency: 'UAH',
  maximumFractionDigits: 0,
});

// Decimal values come from the API as strings ("1200.00")
export function formatMoney(amount) {
  return money.format(Number(amount));
}

// Ukrainian plural forms: 1 день, 2 дні, 5 днів
export function plural(n, one, few, many) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}

export const days = (n) => `${n} ${plural(n, 'день', 'дні', 'днів')}`;
export const visits = (n) => `${n} ${plural(n, 'відвідування', 'відвідування', 'відвідувань')}`;

// The API's days_left counts days after today, so 0 means "today is the last day"
export function daysLeftLabel(membership) {
  if (membership.start_date > dayjs().format(ISO_DATE)) {
    return `Почнеться ${dayjs(membership.start_date).format('DD.MM.YYYY')}`;
  }
  if (membership.days_left === 0) return 'Сьогодні останній день';
  return `Залишилось ${days(membership.days_left)}`;
}

export function initials(fullName) {
  return fullName
    .split(' ')
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
}

export const TARIFF_TYPE_LABELS = {
  single_visit: 'Разове',
  monthly: 'Місячний',
  half_yearly: 'Піврічний',
  yearly: 'Річний',
  visit_pack: 'Пакет відвідувань',
};

// Shortest to longest, then cheaper first — independent of the order tariffs were added in
const TARIFF_TYPE_ORDER = ['single_visit', 'visit_pack', 'monthly', 'half_yearly', 'yearly'];

export function sortTariffs(tariffs) {
  return [...tariffs].sort(
    (a, b) =>
      TARIFF_TYPE_ORDER.indexOf(a.type) - TARIFF_TYPE_ORDER.indexOf(b.type) ||
      Number(a.price) - Number(b.price),
  );
}

export function tariffSummary(tariff) {
  const limit = tariff.visit_limit ? visits(tariff.visit_limit) : 'безліміт відвідувань';
  return `${days(tariff.duration_days)} · ${limit}`;
}

export const MEMBERSHIP_STATUS = {
  pending: { label: 'Очікує оплати', color: 'orange' },
  active: { label: 'Активний', color: 'green' },
  frozen: { label: 'Заморожений', color: 'blue' },
  expired: { label: 'Прострочений', color: 'red' },
  cancelled: { label: 'Скасований', color: 'default' },
};

export const BOOKING_STATUS = {
  booked: { label: 'Записаний', color: 'orange' },
  cancelled: { label: 'Скасовано', color: 'default' },
  attended: { label: 'Відвідано', color: 'green' },
};

export const DISCOUNT_LABELS = {
  student: 'Студентська',
  loyalty: 'Постійний клієнт',
  promo: 'Промокод',
};

export const CHANNEL_LABELS = {
  email: 'Email',
  sms: 'SMS',
  in_app: 'У застосунку',
};

export const WEEKDAYS_SHORT = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'];

// "08:00:00" -> "08:00"
export const hhmm = (time) => time.slice(0, 5);

// Club hours {"0": ["07:00", "22:00"], ...} -> [{ days: "Пн–Пт", hours: "07:00–22:00" }, ...]
export function groupOpeningHours(openingHours) {
  const rows = [];
  for (let day = 0; day < 7; day += 1) {
    const span = openingHours[String(day)];
    const hours = span?.length === 2 ? `${hhmm(span[0])}–${hhmm(span[1])}` : 'вихідний';
    const last = rows.at(-1);
    if (last && last.hours === hours && last.to === day - 1) last.to = day;
    else rows.push({ from: day, to: day, hours });
  }
  return rows.map(({ from, to, hours }) => ({
    days: from === to ? WEEKDAYS_SHORT[from] : `${WEEKDAYS_SHORT[from]}–${WEEKDAYS_SHORT[to]}`,
    hours,
  }));
}

export const WEEKDAYS = [
  'Понеділок',
  'Вівторок',
  'Середа',
  'Четвер',
  'Пʼятниця',
  'Субота',
  'Неділя',
];
