import dayjs from 'dayjs';
import 'dayjs/locale/uk';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.locale('uk');

// Same zone as CLUB_TIMEZONE on the server (backend/app/core/clock.py)
export const CLUB_TZ = 'Europe/Kyiv';

// "2026-11-09" + "18:00" -> "2026-11-09T18:00:00+02:00": the offset follows Kyiv's DST rules for that
// date, not the browser's zone and not today's offset
export function toClubIso(date, time) {
  return dayjs.tz(`${date} ${time}`, 'YYYY-MM-DD HH:mm', CLUB_TZ).format();
}

const OFFSET_RE = /([+-])(\d{2}):?(\d{2})$/;

// The server sends session and visit times in the club time zone (e.g. "...T18:00:00+02:00").
// dayjs(iso) would convert them to the browser zone; clubTime keeps the club's offset instead,
// so 18:00 stays 18:00 for a user whose computer is set to another zone.
export function clubTime(iso) {
  const match = OFFSET_RE.exec(iso);
  if (!match) return dayjs(iso);
  const sign = match[1] === '-' ? -1 : 1;
  return dayjs.utc(iso).utcOffset(sign * (Number(match[2]) * 60 + Number(match[3])));
}

// Monday of the week that contains the given day
export function weekStart(day) {
  const d = dayjs(day);
  return d.subtract((d.day() + 6) % 7, 'day').startOf('day');
}

export const ISO_DATE = 'YYYY-MM-DD';

export { dayjs };
