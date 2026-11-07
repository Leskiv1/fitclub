import { useCallback, useState } from 'react';
import { UndoOutlined } from '@ant-design/icons';
import { App, Button, Empty, Flex, Popconfirm, Segmented, Typography } from 'antd';
import { cancelBooking, fetchClientBookings, undoLastBookingAction } from '../../api/bookings';
import useAuth from '../../auth/useAuth';
import LoadError from '../../components/LoadError';
import PageSpinner from '../../components/PageSpinner';
import SessionRow from '../../components/SessionRow';
import { BookingStatusTag } from '../../components/StatusTag';
import useApi from '../../hooks/useApi';
import { clubTime, dayjs } from '../../utils/dates';
import { getErrorMessage } from '../../utils/errors';

const { Title, Text } = Typography;

function BookingItem({ booking, onCancel }) {
  const start = clubTime(booking.session.start_at);
  const canCancel = booking.status === 'booked' && start.isAfter(dayjs());
  const day = start.format('dddd, D MMMM');

  return (
    <Flex vertical gap={8}>
      <Text type="secondary">{day[0].toUpperCase() + day.slice(1)}</Text>
      <SessionRow
        session={booking.session}
        showPlaces={false}
        extra={
          <Flex gap={8} align="center">
            <BookingStatusTag status={booking.status} />
            {canCancel && (
              <Popconfirm
                title="Скасувати запис?"
                description="Місце звільниться для інших клієнтів"
                okText="Так"
                cancelText="Ні"
                onConfirm={() => onCancel(booking)}
              >
                <Button size="small" danger>
                  Скасувати
                </Button>
              </Popconfirm>
            )}
          </Flex>
        }
      />
    </Flex>
  );
}

// "Мої записи" (Ф-4): cancel a booking or undo the last action (Command with undo on the server)
export default function MyBookingsPage() {
  const { user } = useAuth();
  const { message } = App.useApp();
  const [upcoming, setUpcoming] = useState(true);
  const [undoing, setUndoing] = useState(false);

  // Upcoming: only active bookings, nearest first (a cancelled one comes back via undo).
  // Past: the full history, cancelled included, newest first.
  const load = useCallback(async () => {
    const list = await fetchClientBookings(user.client_id, upcoming);
    return upcoming ? list.filter((b) => b.status !== 'cancelled') : list.reverse();
  }, [user.client_id, upcoming]);
  const { data: bookings, error, loading, reload } = useApi(load);

  const cancel = async (booking) => {
    try {
      await cancelBooking(booking.id);
      message.info('Запис скасовано. Його можна повернути кнопкою «Відмінити останню дію».');
      reload();
    } catch (err) {
      message.error(getErrorMessage(err));
    }
  };

  const undo = async () => {
    setUndoing(true);
    try {
      const { undone, booking } = await undoLastBookingAction();
      const title = booking.session.title ?? 'індивідуальне заняття';
      message.success(
        undone === 'book' ? `Запис на «${title}» відмінено` : `Запис на «${title}» відновлено`,
      );
      reload();
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setUndoing(false);
    }
  };

  return (
    <>
      <Flex justify="space-between" align="start" wrap gap={8}>
        <div>
          <Title level={2} className="page-title">
            Мої записи
          </Title>
          <Text className="page-subtitle">Групові та персональні заняття</Text>
        </div>
        <Popconfirm
          title="Відмінити останню дію?"
          description="Якщо останньою дією був запис — його скасуємо, якщо скасування — запис відновимо"
          okText="Так"
          cancelText="Ні"
          onConfirm={undo}
        >
          <Button icon={<UndoOutlined />} loading={undoing}>
            Відмінити останню дію
          </Button>
        </Popconfirm>
      </Flex>

      <Segmented
        value={upcoming}
        onChange={setUpcoming}
        options={[
          { value: true, label: 'Майбутні' },
          { value: false, label: 'Минулі' },
        ]}
        style={{ marginBottom: 16 }}
      />

      {error && !bookings && <LoadError error={error} onRetry={reload} />}
      {loading && !bookings && <PageSpinner />}
      {bookings && (
        <Flex vertical gap={16} style={{ opacity: loading ? 0.6 : 1 }}>
          {bookings.length ? (
            bookings.map((b) => <BookingItem key={b.id} booking={b} onCancel={cancel} />)
          ) : (
            <Empty description={upcoming ? 'Майбутніх записів немає' : 'Минулих записів немає'} />
          )}
        </Flex>
      )}
    </>
  );
}
