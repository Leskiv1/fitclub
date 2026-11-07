import { useCallback, useState } from 'react';
import { CheckCircleOutlined, ClockCircleOutlined, UserOutlined } from '@ant-design/icons';
import { Button, Card, Col, Empty, Flex, Row, Typography } from 'antd';
import { Link } from 'react-router-dom';
import { bookIndividual } from '../../api/bookings';
import { fetchTrainers } from '../../api/catalog';
import { fetchTrainerSlots } from '../../api/sessions';
import BookingErrorAlert from '../../components/BookingErrorAlert';
import LoadError from '../../components/LoadError';
import PageSpinner from '../../components/PageSpinner';
import TrainerAvatar from '../../components/TrainerAvatar';
import useApi from '../../hooks/useApi';
import useBookingNotice from '../../hooks/useBookingNotice';
import { clubTime, dayjs, ISO_DATE } from '../../utils/dates';

const { Title, Text } = Typography;
const DAYS_AHEAD = 14;

// Monday = 0, as in WorkShift.weekday on the server
const weekday = (d) => (d.day() + 6) % 7;

function StepTitle({ n, children }) {
  return (
    <Title level={4} style={{ marginTop: 32 }}>
      <span style={{ color: 'var(--fc-primary)' }}>{n}.</span> {children}
    </Title>
  );
}

// Ф-4: individual session — trainer -> day -> free slot (from the trainer's shifts) -> confirm
export default function IndividualBookingPage() {
  const { data: trainers, error, reload } = useApi(fetchTrainers);
  const [trainerId, setTrainerId] = useState(null);
  const [date, setDate] = useState(null);
  const [slot, setSlot] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [bookError, setBookError] = useState(null);

  const loadSlots = useCallback(
    () => (trainerId && date ? fetchTrainerSlots(trainerId, date) : Promise.resolve([])),
    [trainerId, date],
  );
  const { data: slots, loading: slotsLoading, reload: reloadSlots } = useApi(loadSlots);
  const notice = useBookingNotice(reloadSlots);

  if (error && !trainers) return <LoadError error={error} onRetry={reload} />;
  if (!trainers) return <PageSpinner />;

  const trainer = trainers.find((t) => t.id === trainerId);
  const workdays = new Set(trainer?.work_shifts.map((s) => s.weekday));
  const today = dayjs().startOf('day');
  const dates = Array.from({ length: DAYS_AHEAD }, (_, i) => today.add(i, 'day'));

  const chooseTrainer = (id) => {
    setTrainerId(id);
    setDate(null);
    setSlot(null);
    setBookError(null);
  };

  const chooseDate = (d) => {
    setDate(d.format(ISO_DATE));
    setSlot(null);
    setBookError(null);
  };

  const confirm = async () => {
    setSubmitting(true);
    setBookError(null);
    try {
      const booking = await bookIndividual(trainerId, slot);
      setSlot(null);
      notice(booking);
      reloadSlots();
    } catch (err) {
      setBookError(err);
    } finally {
      setSubmitting(false);
    }
  };

  const slotStart = slot && clubTime(slot);

  return (
    <>
      <Flex justify="space-between" align="start" wrap gap={8}>
        <div>
          <Title level={2} className="page-title">
            Персональні заняття
          </Title>
          <Text className="page-subtitle">Оберіть тренера, дату та зручний час</Text>
        </div>
        <Link to="/my/bookings">
          <Button>Мої записи</Button>
        </Link>
      </Flex>

      <StepTitle n={1}>Оберіть тренера</StepTitle>
      <Row gutter={[16, 16]}>
        {trainers.map((t) => (
          <Col key={t.id} xs={24} sm={12} lg={6}>
            <div
              role="button"
              tabIndex={0}
              className={`select-card ${t.id === trainerId ? 'select-card--active' : ''}`}
              onClick={() => chooseTrainer(t.id)}
              onKeyDown={(e) => e.key === 'Enter' && chooseTrainer(t.id)}
              style={{ padding: 16, background: t.id === trainerId ? undefined : '#fff' }}
            >
              <Flex gap={12} align="center">
                <TrainerAvatar trainer={t} />
                <Flex vertical style={{ minWidth: 0 }}>
                  <Text strong ellipsis>
                    {t.full_name}
                  </Text>
                  <Text type="secondary" ellipsis>
                    {t.specialization}
                  </Text>
                </Flex>
              </Flex>
            </div>
          </Col>
        ))}
      </Row>

      {trainer && (
        <>
          <StepTitle n={2}>Оберіть дату</StepTitle>
          <div className="chip-row">
            {dates.map((d) => {
              const value = d.format(ISO_DATE);
              return (
                <button
                  key={value}
                  type="button"
                  className={`day-chip ${value === date ? 'day-chip--active' : ''}`}
                  disabled={!workdays.has(weekday(d))}
                  onClick={() => chooseDate(d)}
                >
                  <small>{d.isSame(today) ? 'Сьогодні' : d.format('dd')}</small>
                  <strong>{d.date()}</strong>
                  <small>{d.format('MMM')}</small>
                </button>
              );
            })}
          </div>
        </>
      )}

      {trainer && date && (
        <>
          <StepTitle n={3}>Вільний час</StepTitle>
          {slotsLoading ? (
            <PageSpinner />
          ) : slots.length ? (
            <Flex gap={8} wrap>
              {slots.map((s) => (
                <Button
                  key={s}
                  size="large"
                  type={s === slot ? 'primary' : 'default'}
                  onClick={() => setSlot(s)}
                  style={{ minWidth: 88 }}
                >
                  {clubTime(s).format('HH:mm')}
                </Button>
              ))}
            </Flex>
          ) : (
            <Empty description="На цей день вільного часу немає" />
          )}
        </>
      )}

      {slotStart && (
        <Card className="soft-card" style={{ marginTop: 32, maxWidth: 480 }}>
          <Title level={5} style={{ marginTop: 0 }}>
            <CheckCircleOutlined style={{ color: 'var(--fc-primary)' }} /> Підсумок
          </Title>
          <Flex vertical gap={8}>
            <Text>
              <UserOutlined /> {trainer.full_name} · {trainer.specialization}
            </Text>
            <Text>
              <ClockCircleOutlined /> {slotStart.format('dddd, D MMMM')},{' '}
              {slotStart.format('HH:mm')}–{slotStart.add(1, 'hour').format('HH:mm')}
            </Text>
            <Text type="secondary">Вільний зал підбирається автоматично</Text>
            <BookingErrorAlert error={bookError} />
            <Button type="primary" size="large" block loading={submitting} onClick={confirm}>
              Підтвердити запис
            </Button>
          </Flex>
        </Card>
      )}
    </>
  );
}
