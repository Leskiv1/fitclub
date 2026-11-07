import { useCallback, useState } from 'react';
import {
  ClockCircleOutlined,
  EnvironmentOutlined,
  LeftOutlined,
  RightOutlined,
} from '@ant-design/icons';
import {
  App,
  Button,
  Card,
  Empty,
  Flex,
  Modal,
  Popconfirm,
  Progress,
  Select,
  Tag,
  Typography,
} from 'antd';
import { bookGroupSession, cancelBooking, fetchClientBookings } from '../../api/bookings';
import { fetchTrainers } from '../../api/catalog';
import { fetchWeekSessions } from '../../api/sessions';
import useAuth from '../../auth/useAuth';
import BookingErrorAlert from '../../components/BookingErrorAlert';
import LoadError from '../../components/LoadError';
import PageSpinner from '../../components/PageSpinner';
import SessionRow, { FreePlacesTag } from '../../components/SessionRow';
import TrainerAvatar from '../../components/TrainerAvatar';
import WeekDayPicker from '../../components/WeekDayPicker';
import useApi from '../../hooks/useApi';
import useBookingNotice from '../../hooks/useBookingNotice';
import { clubTime, dayjs, ISO_DATE, weekStart } from '../../utils/dates';

const { Title, Text } = Typography;

function SessionModal({ session, booking, trainer, onClose, onChanged }) {
  const { message } = App.useApp();
  const notice = useBookingNotice(onChanged);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const start = clubTime(session.start_at);
  const end = clubTime(session.end_at);
  const started = start.isBefore(dayjs());

  const book = async () => {
    setBusy(true);
    setError(null);
    try {
      const created = await bookGroupSession(session.id);
      onClose();
      notice(created);
      onChanged();
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  const cancel = async () => {
    setBusy(true);
    try {
      await cancelBooking(booking.id);
      message.info('Запис скасовано');
      onClose();
      onChanged();
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  let footer;
  if (booking) {
    footer = (
      <Flex justify="space-between" align="center">
        <Tag color="green">Ви записані</Tag>
        {!started && (
          <Popconfirm title="Скасувати запис?" okText="Так" cancelText="Ні" onConfirm={cancel}>
            <Button danger loading={busy}>
              Скасувати запис
            </Button>
          </Popconfirm>
        )}
      </Flex>
    );
  } else {
    footer = (
      <Button
        type="primary"
        size="large"
        block
        loading={busy}
        disabled={started || session.free_places <= 0}
        onClick={book}
      >
        {started ? 'Заняття вже почалося' : 'Записатися на заняття'}
      </Button>
    );
  }

  return (
    <Modal open title={session.title} onCancel={onClose} footer={footer} destroyOnHidden>
      <Flex vertical gap={16}>
        <Flex gap={12} wrap>
          <Card size="small" style={{ flex: 1, minWidth: 180 }}>
            <Text type="secondary">
              <ClockCircleOutlined /> Час
            </Text>
            <div>
              <Text strong>
                {start.format('dd, D MMMM')} · {start.format('HH:mm')}–{end.format('HH:mm')}
              </Text>
            </div>
            <Text type="secondary">{end.diff(start, 'minute')} хв</Text>
          </Card>
          <Card size="small" style={{ flex: 1, minWidth: 180 }}>
            <Text type="secondary">
              <EnvironmentOutlined /> Зал
            </Text>
            <div>
              <Text strong>{session.hall.name}</Text>
            </div>
          </Card>
        </Flex>

        <Flex gap={12} align="center">
          <TrainerAvatar trainer={trainer ?? session.trainer} />
          <Flex vertical>
            <Text strong>{session.trainer.full_name}</Text>
            <Text type="secondary">{session.trainer.specialization}</Text>
          </Flex>
        </Flex>

        <div>
          <Flex justify="space-between">
            <Text strong>Доступність місць</Text>
            <FreePlacesTag session={session} />
          </Flex>
          <Progress
            percent={Math.round((session.booked / session.capacity) * 100)}
            showInfo={false}
            strokeColor="#ff6b35"
          />
          <Text type="secondary">
            Записано: {session.booked} · ліміт групи: {session.capacity}
          </Text>
        </div>

        <BookingErrorAlert error={error} />
      </Flex>
    </Modal>
  );
}

// Ф-4: weekly group schedule with booking (rules are checked on the server)
export default function SchedulePage() {
  const { user } = useAuth();
  const thisMonday = weekStart(dayjs());
  const [weekOffset, setWeekOffset] = useState(0);
  const [day, setDay] = useState(() => (dayjs().day() + 6) % 7);
  const [trainerId, setTrainerId] = useState();
  const [selectedId, setSelectedId] = useState(null);

  const monday = thisMonday.add(weekOffset, 'week');
  const clientId = user.client_id;

  const load = useCallback(async () => {
    const week = weekStart(dayjs()).add(weekOffset, 'week').format(ISO_DATE);
    const [sessions, bookings] = await Promise.all([
      fetchWeekSessions({ week, kind: 'group', trainerId }),
      fetchClientBookings(clientId, true),
    ]);
    const bookingBySession = new Map(
      bookings.filter((b) => b.status === 'booked').map((b) => [b.session.id, b]),
    );
    return { sessions, bookingBySession };
  }, [weekOffset, trainerId, clientId]);
  const { data, error, loading, reload } = useApi(load);
  const { data: trainers } = useApi(fetchTrainers);

  if (error && !data) return <LoadError error={error} onRetry={reload} />;

  const selectedDate = monday.add(day, 'day').format(ISO_DATE);
  const daySessions = (data?.sessions ?? []).filter(
    (s) => clubTime(s.start_at).format(ISO_DATE) === selectedDate,
  );
  const selected = data?.sessions.find((s) => s.id === selectedId);

  return (
    <>
      <Title level={2} className="page-title">
        Розклад занять
      </Title>
      <Text className="page-subtitle">
        Групові тренування. Натисніть на заняття, щоб записатися.
      </Text>

      <Flex justify="space-between" align="center" gap={12} wrap style={{ marginBottom: 16 }}>
        <Flex align="center" gap={8}>
          <Button
            icon={<LeftOutlined />}
            aria-label="Попередній тиждень"
            disabled={weekOffset === 0}
            onClick={() => setWeekOffset((w) => w - 1)}
          />
          <Text strong style={{ minWidth: 150, textAlign: 'center' }}>
            {monday.format('D MMM')} – {monday.add(6, 'day').format('D MMM YYYY')}
          </Text>
          <Button
            icon={<RightOutlined />}
            aria-label="Наступний тиждень"
            onClick={() => setWeekOffset((w) => w + 1)}
          />
        </Flex>
        <Select
          allowClear
          placeholder="Усі тренери"
          style={{ minWidth: 220 }}
          value={trainerId}
          onChange={setTrainerId}
          options={(trainers ?? []).map((t) => ({ value: t.id, label: t.full_name }))}
        />
      </Flex>

      <WeekDayPicker monday={monday} value={day} onChange={setDay} />

      <Flex vertical gap={12} style={{ marginTop: 16 }}>
        {loading && !data && <PageSpinner />}
        {data &&
          (daySessions.length ? (
            daySessions.map((s) => (
              <SessionRow
                key={s.id}
                session={s}
                onClick={() => setSelectedId(s.id)}
                extra={data.bookingBySession.has(s.id) && <Tag color="green">Ви записані</Tag>}
              />
            ))
          ) : (
            <Empty description="Цього дня групових занять немає" />
          ))}
      </Flex>

      {selected && (
        <SessionModal
          session={selected}
          booking={data.bookingBySession.get(selected.id)}
          trainer={trainers?.find((t) => t.id === selected.trainer.id)}
          onClose={() => setSelectedId(null)}
          onChanged={reload}
        />
      )}
    </>
  );
}
