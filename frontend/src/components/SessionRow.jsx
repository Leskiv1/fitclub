import { Flex, Tag, Typography } from 'antd';
import { clubTime } from '../utils/dates';

const { Text } = Typography;

export function FreePlacesTag({ session }) {
  if (session.free_places <= 0) return <Tag color="red">Місць немає</Tag>;
  return (
    <Tag color="green">
      {session.free_places} з {session.capacity} вільні
    </Tag>
  );
}

// One training session in a list: time, title, trainer and hall, free places (for the schedule)
export default function SessionRow({ session, onClick, extra, showPlaces = true }) {
  return (
    <div
      className="session-row"
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={(e) => onClick && e.key === 'Enter' && onClick()}
    >
      <Flex vertical className="session-row__time">
        <span>{clubTime(session.start_at).format('HH:mm')}</span>
        <Text type="secondary" style={{ fontSize: 12, fontWeight: 400 }}>
          {clubTime(session.end_at).format('HH:mm')}
        </Text>
      </Flex>
      <Flex vertical style={{ flex: 1, minWidth: 0 }}>
        <Text strong ellipsis>
          {session.title ?? 'Індивідуальне заняття'}
        </Text>
        <Text type="secondary" ellipsis>
          {session.hall.name} · {session.trainer.full_name}
        </Text>
      </Flex>
      <Flex vertical align="end" gap={4}>
        {showPlaces && session.kind === 'group' && <FreePlacesTag session={session} />}
        {extra}
      </Flex>
    </div>
  );
}
