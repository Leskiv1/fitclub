import { useState } from 'react';
import { Alert, Button, Card, DatePicker, Flex, Form, Input, Radio, Typography } from 'antd';
import { Link, Navigate } from 'react-router-dom';
import { homePathFor } from '../auth/roles';
import useAuth from '../auth/useAuth';
import BackHomeLink from '../components/BackHomeLink';
import { dayjs, ISO_DATE } from '../utils/dates';
import { getErrorMessage } from '../utils/errors';
import { CHANNEL_LABELS } from '../utils/format';
import {
  emailRules,
  nameRules,
  normalizePhone,
  passwordRules,
  phoneRules,
} from '../utils/validation';

const { Title, Text } = Typography;

// Guest -> client (use case "Зареєструватися"); the server returns a token right away
export default function RegisterPage() {
  const { user, signUp } = useAuth();
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to={homePathFor(user)} replace />;

  const onFinish = async (values) => {
    setSubmitting(true);
    setError(null);
    try {
      await signUp({
        full_name: values.full_name.trim(),
        birth_date: values.birth_date.format(ISO_DATE),
        phone: values.phone,
        email: values.email,
        password: values.password,
        notification_channel: values.notification_channel,
      });
      // The re-render with a signed-in user redirects to the cabinet
    } catch (err) {
      setError(getErrorMessage(err));
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <BackHomeLink />
      <Flex justify="center">
        <Card className="soft-card" style={{ width: '100%', maxWidth: 480 }}>
          <Title level={2} className="page-title">
            Реєстрація
          </Title>
          <Text className="page-subtitle">Створіть обліковий запис клієнта FitClub</Text>

          {error && <Alert type="error" title={error} showIcon style={{ marginBottom: 16 }} />}

          <Form
            layout="vertical"
            onFinish={onFinish}
            requiredMark={false}
            initialValues={{ notification_channel: 'email' }}
          >
            <Form.Item name="full_name" label="Прізвище та імʼя" rules={nameRules}>
              <Input autoComplete="name" placeholder="Шевченко Тарас" />
            </Form.Item>
            <Form.Item
              name="birth_date"
              label="Дата народження"
              rules={[{ required: true, message: 'Оберіть дату народження' }]}
            >
              <DatePicker
                format="DD.MM.YYYY"
                style={{ width: '100%' }}
                disabledDate={(d) => d.isAfter(dayjs())}
                defaultPickerValue={dayjs().subtract(20, 'year')}
              />
            </Form.Item>
            <Form.Item name="phone" label="Телефон" normalize={normalizePhone} rules={phoneRules}>
              <Input autoComplete="tel" placeholder="+380671234567" />
            </Form.Item>
            <Form.Item name="email" label="Email" rules={emailRules}>
              <Input autoComplete="email" />
            </Form.Item>
            <Form.Item name="password" label="Пароль" rules={passwordRules}>
              <Input.Password autoComplete="new-password" />
            </Form.Item>
            <Form.Item
              name="password_confirm"
              label="Повторіть пароль"
              dependencies={['password']}
              rules={[
                { required: true, message: 'Повторіть пароль' },
                ({ getFieldValue }) => ({
                  validator: (_, value) =>
                    !value || getFieldValue('password') === value
                      ? Promise.resolve()
                      : Promise.reject(new Error('Паролі не збігаються')),
                }),
              ]}
            >
              <Input.Password autoComplete="new-password" />
            </Form.Item>
            <Form.Item name="notification_channel" label="Як повідомляти про закінчення абонемента">
              <Radio.Group
                optionType="button"
                options={Object.entries(CHANNEL_LABELS).map(([value, label]) => ({ value, label }))}
              />
            </Form.Item>
            <Button type="primary" htmlType="submit" size="large" block loading={submitting}>
              Зареєструватися
            </Button>
          </Form>

          <Text style={{ display: 'block', marginTop: 16, textAlign: 'center' }}>
            Уже є обліковий запис? <Link to="/login">Увійти</Link>
          </Text>
        </Card>
      </Flex>
    </div>
  );
}
