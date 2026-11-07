import { useCallback, useState } from 'react';
import { CopyOutlined, PlusOutlined } from '@ant-design/icons';
import {
  Alert,
  App,
  Button,
  DatePicker,
  Flex,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Tag,
  TimePicker,
  Typography,
} from 'antd';
import { fetchHalls, fetchTrainers } from '../../api/catalog';
import { copyWeek, deleteSession, fetchWeekSessions, saveSession } from '../../api/sessions';
import PageHeader from '../../components/PageHeader';
import PageSpinner from '../../components/PageSpinner';
import SessionRow from '../../components/SessionRow';
import ParticipantsModal from '../../components/staff/ParticipantsModal';
import WeekNavigator from '../../components/staff/WeekNavigator';
import useApi from '../../hooks/useApi';
import { clubTime, dayjs, ISO_DATE, toClubIso, weekStart } from '../../utils/dates';
import { getErrorMessage } from '../../utils/errors';
import { WEEKDAYS } from '../../utils/format';

const { Text } = Typography;

async function loadRefs() {
  const [trainers, halls] = await Promise.all([fetchTrainers(), fetchHalls()]);
  return { trainers, halls };
}

// Create or edit a group session; times are sent in the club's zone (DST-aware)
function SessionFormModal({ session, day, refs, onClose, onSaved, onShowParticipants }) {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const initial = session
    ? {
        title: session.title,
        trainer_id: session.trainer.id,
        hall_id: session.hall.id,
        date: dayjs(clubTime(session.start_at).format(ISO_DATE)),
        time: [
          dayjs(clubTime(session.start_at).format('YYYY-MM-DD HH:mm')),
          dayjs(clubTime(session.end_at).format('YYYY-MM-DD HH:mm')),
        ],
        max_participants: session.capacity,
      }
    : { date: day, max_participants: 15 };

  const submit = async () => {
    let v;
    try {
      v = await form.validateFields();
    } catch {
      return;
    }
    const date = v.date.format(ISO_DATE);
    setSaving(true);
    setError(null);
    try {
      await saveSession(session?.id, {
        title: v.title.trim(),
        trainer_id: v.trainer_id,
        hall_id: v.hall_id,
        start_at: toClubIso(date, v.time[0].format('HH:mm')),
        end_at: toClubIso(date, v.time[1].format('HH:mm')),
        max_participants: v.max_participants,
      });
      message.success('Заняття збережено');
      onSaved();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    try {
      await deleteSession(session.id);
      message.success('Заняття видалено');
      onSaved();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  return (
    <Modal
      open
      title={session ? 'Змінити заняття' : 'Нове групове заняття'}
      onCancel={onClose}
      destroyOnHidden
      footer={
        <Flex justify="space-between" wrap gap={8}>
          <Flex gap={8}>
            {session && (
              <>
                <Popconfirm
                  title="Видалити заняття?"
                  description="Можна лише без записів"
                  okText="Видалити"
                  okButtonProps={{ danger: true }}
                  cancelText="Ні"
                  onConfirm={remove}
                >
                  <Button danger>Видалити</Button>
                </Popconfirm>
                <Button onClick={() => onShowParticipants(session)}>
                  Записані: {session.booked}
                </Button>
              </>
            )}
          </Flex>
          <Flex gap={8}>
            <Button onClick={onClose}>Скасувати</Button>
            <Button type="primary" loading={saving} onClick={submit}>
              Зберегти
            </Button>
          </Flex>
        </Flex>
      }
    >
      {error && <Alert type="error" showIcon title={error} style={{ marginBottom: 16 }} />}
      <Form form={form} layout="vertical" requiredMark={false} initialValues={initial}>
        <Form.Item
          name="title"
          label="Назва"
          rules={[
            { required: true, whitespace: true, min: 2, max: 150, message: 'Від 2 символів' },
          ]}
        >
          <Input placeholder="Ранкова йога" />
        </Form.Item>
        <Form.Item
          name="trainer_id"
          label="Тренер"
          rules={[{ required: true, message: 'Оберіть тренера' }]}
        >
          <Select options={refs.trainers.map((t) => ({ value: t.id, label: t.full_name }))} />
        </Form.Item>
        <Form.Item name="hall_id" label="Зал" rules={[{ required: true, message: 'Оберіть зал' }]}>
          <Select
            options={refs.halls.map((h) => ({
              value: h.id,
              label: `${h.name} (до ${h.capacity})`,
            }))}
          />
        </Form.Item>
        <Flex gap={12} wrap>
          <Form.Item name="date" label="Дата" rules={[{ required: true }]} style={{ flex: 1 }}>
            <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="time"
            label="Час"
            rules={[{ required: true, message: 'Оберіть час' }]}
            style={{ flex: 1 }}
          >
            <TimePicker.RangePicker format="HH:mm" minuteStep={5} style={{ width: '100%' }} />
          </Form.Item>
        </Flex>
        <Form.Item name="max_participants" label="Місць у групі" rules={[{ required: true }]}>
          <InputNumber min={1} max={1000} style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Modal>
  );
}

// Prototype on the server: every group session of this week is cloned to the chosen week
function CopyWeekModal({ monday, onClose, onCopied }) {
  const [target, setTarget] = useState(monday.add(1, 'week'));
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const copy = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await copyWeek(monday.format(ISO_DATE), weekStart(target).format(ISO_DATE));
      setResult(res);
      onCopied();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open
      title="Скопіювати групові заняття тижня"
      onCancel={onClose}
      okText={result ? 'Готово' : 'Скопіювати'}
      onOk={result ? onClose : copy}
      confirmLoading={busy}
      cancelButtonProps={{ style: result ? { display: 'none' } : undefined }}
    >
      <Text>
        З тижня {monday.format('D MMM')} – {monday.add(6, 'day').format('D MMM')} на тиждень:
      </Text>
      <DatePicker
        picker="week"
        value={target}
        onChange={(d) => d && setTarget(d)}
        disabled={Boolean(result)}
        format={(d) =>
          `${weekStart(d).format('D MMM')} – ${weekStart(d).add(6, 'day').format('D MMM YYYY')}`
        }
        style={{ width: '100%', marginTop: 8 }}
      />
      {error && <Alert type="error" showIcon title={error} style={{ marginTop: 16 }} />}
      {result && (
        <>
          <Alert
            type="success"
            showIcon
            style={{ marginTop: 16 }}
            title={`Створено занять: ${result.created.length}`}
          />
          {result.skipped.length > 0 && (
            <Flex vertical gap={4} style={{ marginTop: 12 }}>
              <Text strong>Пропущено через конфлікти: {result.skipped.length}</Text>
              {result.skipped.map((s) => (
                <Text key={`${s.title}-${s.start_at}`} type="secondary">
                  {s.title}, {clubTime(s.start_at).format('dd D MMM, HH:mm')} — {s.reason}
                </Text>
              ))}
            </Flex>
          )}
        </>
      )}
    </Modal>
  );
}

// Ф-4 (admin): weekly schedule of group sessions; individual ones are shown for the full picture
export default function AdminSchedulePage() {
  const [offset, setOffset] = useState(0);
  const [editing, setEditing] = useState(null); // { session?, day }
  const [participantsOf, setParticipantsOf] = useState(null);
  const [copying, setCopying] = useState(false);
  const monday = weekStart(dayjs()).add(offset, 'week');

  const load = useCallback(
    () => fetchWeekSessions({ week: weekStart(dayjs()).add(offset, 'week').format(ISO_DATE) }),
    [offset],
  );
  const { data: sessions, loading, reload } = useApi(load);
  const { data: refs } = useApi(loadRefs);

  const open = (session) =>
    session.kind === 'group' ? setEditing({ session }) : setParticipantsOf(session);

  return (
    <>
      <PageHeader
        title="Розклад"
        subtitle="Групові заняття тижня; індивідуальні створюють клієнти"
        extra={
          <>
            <Button icon={<CopyOutlined />} onClick={() => setCopying(true)}>
              Скопіювати тиждень
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              disabled={!refs}
              onClick={() => setEditing({ day: dayjs() })}
            >
              Додати заняття
            </Button>
          </>
        }
      />
      <WeekNavigator monday={monday} offset={offset} onShift={(d) => setOffset((o) => o + d)} />
      {loading && !sessions && <PageSpinner />}
      <Flex vertical gap={16} style={{ marginTop: 16, opacity: loading ? 0.6 : 1 }}>
        {WEEKDAYS.map((name, i) => {
          const day = monday.add(i, 'day');
          const daySessions = (sessions ?? []).filter(
            (s) => clubTime(s.start_at).format(ISO_DATE) === day.format(ISO_DATE),
          );
          return (
            <div key={name}>
              <Flex justify="space-between" align="center">
                <Text type="secondary">
                  {name}, {day.format('D MMMM')}
                </Text>
                <Button
                  size="small"
                  type="text"
                  icon={<PlusOutlined />}
                  disabled={!refs}
                  onClick={() => setEditing({ day })}
                  aria-label={`Додати заняття: ${name}`}
                />
              </Flex>
              <Flex vertical gap={8} style={{ marginTop: 4 }}>
                {daySessions.length ? (
                  daySessions.map((s) => (
                    <SessionRow
                      key={s.id}
                      session={s}
                      onClick={() => open(s)}
                      extra={s.kind === 'individual' && <Tag color="blue">Індивідуальне</Tag>}
                    />
                  ))
                ) : (
                  <Text type="secondary">—</Text>
                )}
              </Flex>
            </div>
          );
        })}
      </Flex>

      {editing && refs && (
        <SessionFormModal
          session={editing.session}
          day={editing.day}
          refs={refs}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            reload();
          }}
          onShowParticipants={setParticipantsOf}
        />
      )}
      {participantsOf && (
        <ParticipantsModal session={participantsOf} onClose={() => setParticipantsOf(null)} />
      )}
      {copying && (
        <CopyWeekModal monday={monday} onClose={() => setCopying(false)} onCopied={reload} />
      )}
    </>
  );
}
