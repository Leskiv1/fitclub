import { LeftOutlined, RightOutlined } from '@ant-design/icons';
import { Button, Flex, Typography } from 'antd';

const { Text } = Typography;

// "‹ 9 лист – 15 лист 2026 ›"; offset is the number of weeks from the current one
export default function WeekNavigator({ monday, onShift, minOffset, offset }) {
  return (
    <Flex align="center" gap={8}>
      <Button
        icon={<LeftOutlined />}
        aria-label="Попередній тиждень"
        disabled={minOffset !== undefined && offset <= minOffset}
        onClick={() => onShift(-1)}
      />
      <Text strong style={{ minWidth: 160, textAlign: 'center' }}>
        {monday.format('D MMM')} – {monday.add(6, 'day').format('D MMM YYYY')}
      </Text>
      <Button icon={<RightOutlined />} aria-label="Наступний тиждень" onClick={() => onShift(1)} />
    </Flex>
  );
}
