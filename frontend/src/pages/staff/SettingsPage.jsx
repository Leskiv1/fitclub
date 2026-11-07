import { useCallback, useState } from 'react';
import { PlayCircleOutlined } from '@ant-design/icons';
import {
  Alert,
  App,
  Button,
  Card,
  Col,
  Flex,
  Form,
  InputNumber,
  Row,
  Select,
  Switch,
  Table,
  Tag,
  TimePicker,
  Typography,
} from 'antd';
import { fetchNotificationLog, runDailyCheck } from '../../api/admin';
import { fetchSettings, updateSettings } from '../../api/catalog';
import LoadError from '../../components/LoadError';
import PageHeader from '../../components/PageHeader';
import PageSpinner from '../../components/PageSpinner';
import WeekHoursInput from '../../components/staff/WeekHoursInput';
import useApi from '../../hooks/useApi';
import { clubTime, dayjs } from '../../utils/dates';
import { getErrorMessage } from '../../utils/errors';
import { CHANNEL_LABELS, days } from '../../utils/format';

const { Text } = Typography;
const LOG_PAGE = 10;

const KIND_LABELS = {
  membership_purchased: 'Оформлення абонемента',
  membership_expiring: 'Закінчення абонемента',
  visits_low: 'Мало відвідувань',
};

const STATUS = {
  sent: { label: 'Надіслано', color: 'green' },
  pending: { label: 'Очікує', color: 'orange' },
  failed: { label: 'Помилка', color: 'red' },
};

const toTime = (value) => dayjs(`2000-01-01 ${value.slice(0, 5)}`);

function SettingsForm({ settings, onSaved }) {
  const { message } = App.useApp();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const save = async (values) => {
    setSaving(true);
    setError(null);
    try {
      onSaved(
        await updateSettings({
          ...values,
          daily_check_time: values.daily_check_time.format('HH:mm'),
        }),
      );
      message.success('Налаштування збережено');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Form
      layout="vertical"
      requiredMark={false}
      onFinish={save}
      initialValues={{ ...settings, daily_check_time: toTime(settings.daily_check_time) }}
    >
      {error && <Alert type="error" showIcon title={error} style={{ marginBottom: 16 }} />}
      <Row gutter={24}>
        <Col xs={24} lg={12}>
          <Form.Item name="opening_hours" label="Години роботи (поза ними check-in заборонено)">
            <WeekHoursInput />
          </Form.Item>
        </Col>
        <Col xs={24} lg={12}>
          <Form.Item
            name="notifications_enabled"
            label="Автоматичні сповіщення про закінчення абонемента"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
          <Form.Item
            name="expiry_warning_days"
            label="Попереджати за, днів"
            rules={[{ required: true }]}
          >
            <InputNumber min={1} max={60} style={{ width: 160 }} />
          </Form.Item>
          <Form.Item
            name="daily_check_time"
            label="Час щоденної перевірки"
            rules={[{ required: true }]}
            extra="Планувальник переводить прострочені абонементи у «Прострочений» і надсилає нагадування"
          >
            <TimePicker format="HH:mm" minuteStep={5} style={{ width: 160 }} />
          </Form.Item>
          <Form.Item name="currency" label="Валюта" rules={[{ required: true }]}>
            <Select style={{ width: 160 }} options={[{ value: 'UAH', label: 'UAH — гривня' }]} />
          </Form.Item>
        </Col>
      </Row>
      <Button type="primary" htmlType="submit" loading={saving}>
        Зберегти налаштування
      </Button>
    </Form>
  );
}

function NotificationLog() {
  const [page, setPage] = useState(1);
  const [kind, setKind] = useState();
  const [status, setStatus] = useState();

  const load = useCallback(
    () => fetchNotificationLog({ offset: (page - 1) * LOG_PAGE, limit: LOG_PAGE, kind, status }),
    [page, kind, status],
  );
  const { data, loading } = useApi(load);

  return (
    <>
      <Flex gap={8} wrap style={{ marginBottom: 12 }}>
        <Select
          allowClear
          placeholder="Тип"
          style={{ width: 220 }}
          value={kind}
          onChange={(v) => {
            setKind(v);
            setPage(1);
          }}
          options={Object.entries(KIND_LABELS).map(([value, label]) => ({ value, label }))}
        />
        <Select
          allowClear
          placeholder="Статус"
          style={{ width: 160 }}
          value={status}
          onChange={(v) => {
            setStatus(v);
            setPage(1);
          }}
          options={Object.entries(STATUS).map(([value, s]) => ({ value, label: s.label }))}
        />
      </Flex>
      <Table
        rowKey="id"
        size="small"
        loading={loading}
        dataSource={data?.items ?? []}
        scroll={{ x: 'max-content' }}
        pagination={{
          current: page,
          pageSize: LOG_PAGE,
          total: data?.total ?? 0,
          onChange: setPage,
          showSizeChanger: false,
        }}
        columns={[
          {
            title: 'Створено',
            dataIndex: 'created_at',
            render: (v) => clubTime(v).format('DD.MM.YYYY HH:mm'),
          },
          { title: 'Клієнт', dataIndex: 'client_name' },
          { title: 'Тип', dataIndex: 'kind', render: (k) => KIND_LABELS[k] },
          { title: 'Канал', dataIndex: 'channel', render: (c) => CHANNEL_LABELS[c] },
          {
            title: 'Повідомлення',
            dataIndex: 'message',
            width: 320,
            render: (m, n) => (
              <Text ellipsis={{ tooltip: m }} style={{ maxWidth: 320 }}>
                {n.subject ? `${n.subject}: ` : ''}
                {m}
              </Text>
            ),
          },
          {
            title: 'Статус',
            dataIndex: 'status',
            render: (s, n) => (
              <Tag color={STATUS[s].color} title={n.error ?? undefined}>
                {STATUS[s].label}
              </Tag>
            ),
          },
        ]}
      />
    </>
  );
}

// ЗВ-7, Ф-6: club settings (Singleton ClubSettings on the server), notification log, manual check
export default function SettingsPage() {
  const { message } = App.useApp();
  const { data: settings, error, reload } = useApi(fetchSettings);
  const [running, setRunning] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  if (error && !settings) return <LoadError error={error} onRetry={reload} />;
  if (!settings) return <PageSpinner />;

  const runCheck = async () => {
    setRunning(true);
    try {
      const result = await runDailyCheck();
      if (result.skipped) message.info('Перевірку вже виконує інший процес');
      else
        message.success(
          `Прострочено абонементів: ${result.expired}, надіслано нагадувань: ${result.reminders}`,
        );
      setRefreshKey((k) => k + 1);
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setRunning(false);
    }
  };

  return (
    <>
      <PageHeader title="Налаштування клубу" subtitle="Години роботи й автоматичні сповіщення" />
      <Card className="soft-card" style={{ marginBottom: 24 }}>
        <SettingsForm settings={settings} onSaved={reload} />
      </Card>
      <Card
        className="soft-card"
        title="Журнал сповіщень"
        extra={
          <Button icon={<PlayCircleOutlined />} loading={running} onClick={runCheck}>
            Виконати перевірку зараз
          </Button>
        }
      >
        <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
          Щоденна перевірка о {settings.daily_check_time.slice(0, 5)}; нагадування — за{' '}
          {days(settings.expiry_warning_days)} до кінця абонемента
          {settings.notifications_enabled ? '' : ' (зараз вимкнено)'}.
        </Text>
        {/* a new key re-mounts the log, so it is read again after a manual check */}
        <NotificationLog key={refreshKey} />
      </Card>
    </>
  );
}
