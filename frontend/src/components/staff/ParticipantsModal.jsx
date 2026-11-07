import { useCallback } from 'react';
import { Modal, Table, Typography } from 'antd';
import { fetchParticipants } from '../../api/sessions';
import useApi from '../../hooks/useApi';
import { clubTime } from '../../utils/dates';
import { BookingStatusTag } from '../StatusTag';

const { Text } = Typography;

// Who is booked for a session (staff or the trainer of that session)
export default function ParticipantsModal({ session, onClose }) {
  const load = useCallback(() => fetchParticipants(session.id), [session.id]);
  const { data, loading } = useApi(load);
  const start = clubTime(session.start_at);

  return (
    <Modal open title={session.title ?? 'Індивідуальне заняття'} onCancel={onClose} footer={null}>
      <Text type="secondary">
        {start.format('dddd, D MMMM')} · {start.format('HH:mm')}–
        {clubTime(session.end_at).format('HH:mm')} · {session.hall.name}
      </Text>
      <Table
        rowKey="booking_id"
        size="small"
        style={{ marginTop: 16 }}
        loading={loading}
        dataSource={data ?? []}
        pagination={false}
        columns={[
          { title: 'Клієнт', dataIndex: 'full_name' },
          { title: 'Телефон', dataIndex: 'phone' },
          { title: 'Статус', dataIndex: 'status', render: (s) => <BookingStatusTag status={s} /> },
        ]}
        locale={{ emptyText: 'Ніхто не записаний' }}
      />
    </Modal>
  );
}
