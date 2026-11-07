import { Checkbox, Flex, TimePicker, Typography } from 'antd';
import { dayjs } from '../../utils/dates';
import { WEEKDAYS } from '../../utils/format';

const { Text } = Typography;
const DEFAULT_SPAN = ['09:00', '18:00'];

// "18:30" or "18:30:00" -> dayjs today at 18:30 (TimePicker works with dayjs values)
const toTime = (value) => {
  const [h, m] = value.split(':').map(Number);
  return dayjs().startOf('day').hour(h).minute(m);
};

// Form control for a weekly timetable: { "0": ["09:00", "18:00"], ... }, a missing day = day off.
// Used for trainers' shifts and the club's opening hours.
export default function WeekHoursInput({ value = {}, onChange }) {
  const set = (day, span) => {
    const next = { ...value };
    if (span) next[day] = span;
    else delete next[day];
    onChange?.(next);
  };

  return (
    <Flex vertical gap={8}>
      {WEEKDAYS.map((name, i) => {
        const day = String(i);
        const span = value[day];
        return (
          <Flex key={day} align="center" gap={12} wrap>
            <Checkbox
              checked={Boolean(span)}
              onChange={(e) => set(day, e.target.checked ? DEFAULT_SPAN : null)}
              style={{ width: 130 }}
            >
              {name}
            </Checkbox>
            {span ? (
              <TimePicker.RangePicker
                format="HH:mm"
                minuteStep={15}
                allowClear={false}
                value={[toTime(span[0]), toTime(span[1])]}
                onChange={(range) =>
                  range &&
                  set(
                    day,
                    range.map((t) => t.format('HH:mm')),
                  )
                }
              />
            ) : (
              <Text type="secondary">вихідний</Text>
            )}
          </Flex>
        );
      })}
    </Flex>
  );
}
