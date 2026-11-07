import { useCallback } from 'react';
import { App, Button } from 'antd';
import { undoLastBookingAction } from '../api/bookings';
import { clubTime } from '../utils/dates';
import { getErrorMessage } from '../utils/errors';

// After a booking: a notification with "Відмінити", which calls the server-side Command undo
export default function useBookingNotice(onChanged) {
  const { notification, message } = App.useApp();

  return useCallback(
    (booking) => {
      const key = `booking-${booking.id}`;
      const start = clubTime(booking.session.start_at);

      const undo = async () => {
        notification.destroy(key);
        try {
          await undoLastBookingAction();
          message.info('Запис відмінено');
          onChanged();
        } catch (error) {
          message.error(getErrorMessage(error));
        }
      };

      notification.success({
        key,
        title: 'Ви записані',
        description: `${booking.session.title ?? 'Індивідуальне заняття'}, ${start.format('D MMMM, HH:mm')}`,
        actions: (
          <Button size="small" onClick={undo}>
            Відмінити
          </Button>
        ),
      });
    },
    [notification, message, onChanged],
  );
}
