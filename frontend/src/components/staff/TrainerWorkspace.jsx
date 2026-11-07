import { useCallback, useState } from 'react';
import { Card, Descriptions, Empty, Flex, Table, Tabs, Tag, Typography } from 'antd';
import { fetchTrainer, fetchTrainerClients } from '../../api/catalog';
import { fetchWeekSessions } from '../../api/sessions';
import useApi from '../../hooks/useApi';
import { clubTime, dayjs, ISO_DATE, weekStart } from '../../utils/dates';
import { hhmm, WEEKDAYS } from '../../utils/format';
import LoadError from '../LoadError';
import PageHeader from '../PageHeader';
import PageSpinner from '../PageSpinner';
import SessionRow from '../SessionRow';
import TrainerAvatar from '../TrainerAvatar';
import ParticipantsModal from './ParticipantsModal';
import WeekNavigator from './WeekNavigator';

const { Text, Paragraph } = Typography;

function WeekSchedule({ trainerId }) {
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState(null);
  const monday = weekStart(dayjs()).add(offset, 'week');

  const load = useCallback(
    () =>
      fetchWeekSessions({
        week: weekStart(dayjs()).add(offset, 'week').format(ISO_DATE),
        trainerId,
      }),
    [offset, trainerId],
  );
  const { data: sessions, loading } = useApi(load);

  return (
    <>
      <WeekNavigator monday={monday} offset={offset} onShift={(d) => setOffset((o) => o + d)} />
      {loading && !sessions && <PageSpinner />}
      <Flex vertical gap={16} style={{ marginTop: 16, opacity: loading ? 0.6 : 1 }}>
        {WEEKDAYS.map((name, i) => {
          const date = monday.add(i, 'day').format(ISO_DATE);
          const daySessions = (sessions ?? []).filter(
            (s) => clubTime(s.start_at).format(ISO_DATE) === date,
          );
          return (
            <div key={name}>
              <Text type="secondary">
                {name}, {monday.add(i, 'day').format('D MMMM')}
              </Text>
              <Flex vertical gap={8} style={{ marginTop: 4 }}>
                {daySessions.length ? (
                  daySessions.map((s) => (
                    <SessionRow
                      key={s.id}
                      session={s}
                      onClick={() => setSelected(s)}
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
      {selected && <ParticipantsModal session={selected} onClose={() => setSelected(null)} />}
    </>
  );
}

function ClientsTab({ trainerId }) {
  const load = useCallback(() => fetchTrainerClients(trainerId), [trainerId]);
  const { data, loading } = useApi(load);
  return (
    <Table
      rowKey="id"
      loading={loading}
      dataSource={data ?? []}
      pagination={{ pageSize: 20, hideOnSinglePage: true }}
      columns={[
        { title: 'Клієнт', dataIndex: 'full_name' },
        { title: 'Телефон', dataIndex: 'phone' },
      ]}
      locale={{ emptyText: <Empty description="Клієнтів поки немає" /> }}
    />
  );
}

function ProfileTab({ trainer }) {
  const shifts = [...trainer.work_shifts].sort((a, b) => a.weekday - b.weekday);
  return (
    <Card className="soft-card">
      <Flex gap={24} wrap>
        <TrainerAvatar trainer={trainer} size={96} />
        <Flex vertical gap={8} style={{ flex: 1, minWidth: 240 }}>
          <Descriptions column={1} size="small">
            <Descriptions.Item label="Спеціалізація">{trainer.specialization}</Descriptions.Item>
            <Descriptions.Item label="Email">{trainer.email}</Descriptions.Item>
          </Descriptions>
          {trainer.bio && <Paragraph>{trainer.bio}</Paragraph>}
          <Text strong>Графік роботи</Text>
          {shifts.length ? (
            shifts.map((s) => (
              <Flex key={s.weekday} justify="space-between" style={{ maxWidth: 320 }}>
                <Text>{WEEKDAYS[s.weekday]}</Text>
                <Text strong>
                  {hhmm(s.start_time)}–{hhmm(s.end_time)}
                </Text>
              </Flex>
            ))
          ) : (
            <Text type="secondary">Зміни не задано</Text>
          )}
        </Flex>
      </Flex>
    </Card>
  );
}

// Ф-3: trainer profile — specialization, work schedule with sessions, list of clients.
// Used by the trainer for themselves and by the admin for any trainer.
export default function TrainerWorkspace({ trainerId, title }) {
  const load = useCallback(() => fetchTrainer(trainerId), [trainerId]);
  const { data: trainer, error, reload } = useApi(load);

  if (error && !trainer) return <LoadError error={error} onRetry={reload} />;
  if (!trainer) return <PageSpinner />;

  return (
    <>
      <PageHeader title={title ?? trainer.full_name} subtitle={trainer.specialization} />
      <Tabs
        items={[
          { key: 'schedule', label: 'Розклад', children: <WeekSchedule trainerId={trainer.id} /> },
          { key: 'clients', label: 'Клієнти', children: <ClientsTab trainerId={trainer.id} /> },
          { key: 'profile', label: 'Профіль', children: <ProfileTab trainer={trainer} /> },
        ]}
      />
    </>
  );
}
