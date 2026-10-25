import { useEffect, useState } from 'react';
import { Card, Flex, Spin, Tag, Typography } from 'antd';
import { fetchHealth } from '../api/health';

const { Title, Text } = Typography;

function StatusTag({ ok, okText, failText }) {
  return <Tag color={ok ? 'success' : 'error'}>{ok ? okText : failText}</Tag>;
}

export default function HomePage() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() => setError(true));
  }, []);

  return (
    <Flex justify="center" align="center" style={{ minHeight: '100vh', padding: 16 }}>
      <Card style={{ width: 420 }}>
        <Title level={2} style={{ marginTop: 0 }}>
          FitClub
        </Title>
        <Text type="secondary">Система управління фітнес-клубом</Text>
        <Flex vertical gap={8} style={{ marginTop: 24 }}>
          {!health && !error && <Spin />}
          {(health || error) && (
            <>
              <Flex justify="space-between">
                <Text>API</Text>
                <StatusTag ok={!error} okText="працює" failText="недоступне" />
              </Flex>
              <Flex justify="space-between">
                <Text>База даних</Text>
                <StatusTag
                  ok={health?.database === 'up'}
                  okText="підключена"
                  failText="недоступна"
                />
              </Flex>
            </>
          )}
        </Flex>
      </Card>
    </Flex>
  );
}
