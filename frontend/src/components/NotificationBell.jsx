import { useCallback } from 'react';
import { BellOutlined } from '@ant-design/icons';
import { Badge, Button, Empty, Flex, Popover, Tag, Typography } from 'antd';
import { fetchClientNotifications } from '../api/clients';
import useApi from '../hooks/useApi';
import { dayjs } from '../utils/dates';
import { CHANNEL_LABELS } from '../utils/format';

const { Text } = Typography;
const RECENT_DAYS = 7;

// Ф-6: notifications the daily job and purchases sent to the client (any channel)
export default function NotificationBell({ clientId }) {
  const load = useCallback(() => fetchClientNotifications(clientId, 10), [clientId]);
  const { data } = useApi(load);
  const items = data?.items ?? [];
  const hasRecent = items.some((n) => dayjs().diff(dayjs(n.created_at), 'day') < RECENT_DAYS);

  const content = items.length ? (
    <Flex vertical gap={12} style={{ width: 320, maxHeight: 400, overflowY: 'auto' }}>
      {items.map((n) => (
        <Flex key={n.id} vertical gap={2}>
          <Flex justify="space-between" gap={8}>
            <Text strong>{n.subject ?? 'Повідомлення'}</Text>
            <Tag>{CHANNEL_LABELS[n.channel]}</Tag>
          </Flex>
          <Text>{n.message}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {dayjs(n.created_at).format('D MMMM, HH:mm')}
          </Text>
        </Flex>
      ))}
    </Flex>
  ) : (
    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Сповіщень немає" />
  );

  return (
    <Popover content={content} title="Сповіщення" trigger="click" placement="bottomRight">
      <Badge dot={hasRecent} offset={[-6, 6]}>
        <Button type="text" shape="circle" icon={<BellOutlined />} aria-label="Сповіщення" />
      </Badge>
    </Popover>
  );
}
