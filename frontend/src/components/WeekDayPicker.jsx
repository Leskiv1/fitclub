import { dayjs } from '../utils/dates';
import { WEEKDAYS_SHORT } from '../utils/format';

// Seven day chips of one week; value is the day index 0 (Mon) .. 6 (Sun)
export default function WeekDayPicker({ monday, value, onChange, isDisabled }) {
  const today = dayjs().startOf('day');

  return (
    <div className="chip-row" role="tablist">
      {WEEKDAYS_SHORT.map((label, index) => {
        const day = monday.add(index, 'day');
        const active = index === value;
        return (
          <button
            key={label}
            type="button"
            role="tab"
            aria-selected={active}
            className={`day-chip ${active ? 'day-chip--active' : ''}`}
            disabled={isDisabled?.(day)}
            onClick={() => onChange(index)}
          >
            <small>{day.isSame(today) ? 'Сьогодні' : label}</small>
            <strong>{day.date()}</strong>
            <small>{day.format('MMM')}</small>
          </button>
        );
      })}
    </div>
  );
}
