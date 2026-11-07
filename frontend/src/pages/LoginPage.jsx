import { useState } from 'react';
import { LockOutlined, MailOutlined } from '@ant-design/icons';
import { Alert, Button, Card, Flex, Form, Input, Typography } from 'antd';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { homePathFor } from '../auth/roles';
import useAuth from '../auth/useAuth';
import BackHomeLink from '../components/BackHomeLink';
import { getErrorMessage } from '../utils/errors';

const { Title, Text } = Typography;

export default function LoginPage() {
  const { user, signIn } = useAuth();
  const location = useLocation();
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // After a successful sign in the re-render lands here: back to the page that asked for it,
  // if that page belongs to the user's role, otherwise to the role's home
  if (user) {
    const home = homePathFor(user);
    const from = location.state?.from;
    return <Navigate to={from?.startsWith(home) ? from : home} replace />;
  }

  const onFinish = async ({ email, password }) => {
    setSubmitting(true);
    setError(null);
    try {
      await signIn(email, password);
    } catch (err) {
      setError(getErrorMessage(err));
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <BackHomeLink />
      <Flex justify="center">
        <Card className="soft-card" style={{ width: '100%', maxWidth: 420 }}>
          <Title level={2} className="page-title">
            Вхід
          </Title>
          <Text className="page-subtitle">
            Увійдіть, щоб записуватися на заняття й купувати абонементи
          </Text>

          {error && <Alert type="error" title={error} showIcon style={{ marginBottom: 16 }} />}

          <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
            <Form.Item
              name="email"
              label="Email"
              rules={[{ required: true, type: 'email', message: 'Введіть коректний email' }]}
            >
              <Input prefix={<MailOutlined />} autoComplete="email" size="large" />
            </Form.Item>
            <Form.Item
              name="password"
              label="Пароль"
              rules={[{ required: true, message: 'Введіть пароль' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                autoComplete="current-password"
                size="large"
              />
            </Form.Item>
            <Button type="primary" htmlType="submit" size="large" block loading={submitting}>
              Увійти
            </Button>
          </Form>

          <Text style={{ display: 'block', marginTop: 16, textAlign: 'center' }}>
            Ще немає облікового запису? <Link to="/register">Зареєструватися</Link>
          </Text>
        </Card>
      </Flex>
    </div>
  );
}
