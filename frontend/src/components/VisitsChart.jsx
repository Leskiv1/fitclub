import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { dayjs, weekStart } from '../utils/dates';
import { visits as visitsLabel } from '../utils/format';

const WEEKS = 8;

// Visits per week for the last WEEKS weeks (visit_date is the club-local date of the check-in)
function byWeek(visitList) {
  const current = weekStart(dayjs());
  const weeks = Array.from({ length: WEEKS }, (_, i) => {
    const start = current.subtract(WEEKS - 1 - i, 'week');
    return { start, label: start.format('DD.MM'), count: 0 };
  });
  for (const visit of visitList) {
    const start = weekStart(visit.visit_date);
    const week = weeks.find((w) => w.start.isSame(start, 'day'));
    if (week) week.count += 1;
  }
  return weeks;
}

export default function VisitsChart({ visits }) {
  const data = byWeek(visits);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -24 }}>
        <XAxis
          dataKey="label"
          tickLine={false}
          axisLine={false}
          fontSize={12}
          interval="preserveStartEnd"
          minTickGap={12}
        />
        <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={12} />
        <Tooltip
          cursor={{ fill: 'var(--fc-surface-low)' }}
          formatter={(value) => [visitsLabel(value), 'Тиждень']}
          labelFormatter={(label) => `з ${label}`}
        />
        <Bar dataKey="count" radius={[6, 6, 0, 0]}>
          {data.map((week, i) => (
            <Cell key={week.label} fill={i === WEEKS - 1 ? '#ff6b35' : '#ffb59d'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
