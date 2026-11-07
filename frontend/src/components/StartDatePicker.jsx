import { DatePicker, Flex, Typography } from 'antd';
import { dayjs, ISO_DATE } from '../utils/dates';

const { Text } = Typography;

// Start date of a new membership. The allowed days come from the server (quote.start_options):
// the club works that day, today only until closing time, at most one month ahead
export default function StartDatePicker({ quote, value, onChange }) {
  const allowed = new Set(quote?.start_options ?? []);
  const earliest = quote?.start_options?.[0];
  const startsLater = earliest && earliest > dayjs().format(ISO_DATE);

  return (
    <Flex vertical gap={4}>
      <DatePicker
        format="DD.MM.YYYY"
        allowClear={false}
        disabled={!quote}
        value={value ? dayjs(value) : quote ? dayjs(quote.start_date) : null}
        disabledDate={(d) => !allowed.has(d.format(ISO_DATE))}
        onChange={(d) => onChange(d.format(ISO_DATE))}
        style={{ width: '100%', maxWidth: 240 }}
      />
      {startsLater && (
        <Text type="secondary" style={{ fontSize: 12 }}>
          Найраніше — з {dayjs(earliest).format('DD.MM.YYYY')}: сьогодні клуб уже зачинений або ще
          діє поточний абонемент
        </Text>
      )}
    </Flex>
  );
}
