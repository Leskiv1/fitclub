import { Flex, Typography } from 'antd';

const { Title, Text } = Typography;

// Page title with an optional subtitle and actions on the right
export default function PageHeader({ title, subtitle, extra }) {
  return (
    <Flex justify="space-between" align="start" wrap gap={12} style={{ marginBottom: 24 }}>
      <div>
        <Title level={2} className="page-title">
          {title}
        </Title>
        {subtitle && (
          <Text type="secondary" style={{ display: 'block' }}>
            {subtitle}
          </Text>
        )}
      </div>
      {extra && (
        <Flex gap={8} wrap>
          {extra}
        </Flex>
      )}
    </Flex>
  );
}
