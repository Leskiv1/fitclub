import { useCallback, useState } from 'react';
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import {
  App,
  Button,
  Card,
  Descriptions,
  Empty,
  Flex,
  Popconfirm,
  Table,
  Tabs,
  Tag,
  Typography,
} from 'antd';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { fetchClientBookings } from '../../api/bookings';
import { deleteClient, fetchClient, fetchClientVisits } from '../../api/clients';
import { changeMembershipState, fetchClientMemberships } from '../../api/memberships';
import { ADMIN } from '../../auth/roles';
import useAuth from '../../auth/useAuth';
import LoadError from '../../components/LoadError';
import PageHeader from '../../components/PageHeader';
import PageSpinner from '../../components/PageSpinner';
import SessionRow from '../../components/SessionRow';
import { BookingStatusTag, MembershipStatusTag } from '../../components/StatusTag';
import ClientFormDrawer from '../../components/staff/ClientFormDrawer';
import SellMembershipModal from '../../components/staff/SellMembershipModal';
import useApi from '../../hooks/useApi';
import { clubTime, dayjs } from '../../utils/dates';
import { getErrorMessage } from '../../utils/errors';
import { CHANNEL_LABELS, DISCOUNT_LABELS, formatMoney } from '../../utils/format';

const { Text } = Typography;
const DATE = 'DD.MM.YYYY';
const VISITS_PAGE = 10;

// Which transitions the State pattern allows from each state (the server enforces the same rules)
const ACTIONS_BY_STATUS = {
  active: [
    { action: 'freeze', label: 'Заморозити' },
    { action: 'cancel', label: 'Скасувати', danger: true },
  ],
  frozen: [
    { action: 'unfreeze', label: 'Розморозити' },
    { action: 'cancel', label: 'Скасувати', danger: true },
  ],
  pending: [{ action: 'cancel', label: 'Скасувати', danger: true }],
};

async function loadClientCard(clientId) {
  const [client, memberships, bookings] = await Promise.all([
    fetchClient(clientId),
    fetchClientMemberships(clientId),
    fetchClientBookings(clientId, true),
  ]);
  return { client, memberships, bookings: bookings.filter((b) => b.status === 'booked') };
}

function MembershipItem({ membership, onAction }) {
  const actions = ACTIONS_BY_STATUS[membership.status] ?? [];
  return (
    <Card size="small">
      <Flex justify="space-between" align="start" gap={8} wrap>
        <Flex vertical gap={2}>
          <Text strong>{membership.tariff.name}</Text>
          <Text type="secondary">
            {dayjs(membership.start_date).format(DATE)} – {dayjs(membership.end_date).format(DATE)}
            {membership.visits_left !== null && ` · залишок ${membership.visits_left}`}
            {membership.status === 'frozen' &&
              ` · заморожено з ${dayjs(membership.frozen_at).format(DATE)}`}
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {formatMoney(membership.total_price)}
            {membership.discount_type &&
              ` · знижка «${DISCOUNT_LABELS[membership.discount_type]}» ${formatMoney(membership.discount_amount)}`}
            {membership.options.length > 0 &&
              ` · ${membership.options.map((o) => o.name).join(', ')}`}
          </Text>
        </Flex>
        <Flex vertical align="end" gap={8}>
          <MembershipStatusTag status={membership.status} />
          <Flex gap={4} wrap justify="end">
            {actions.map(({ action, label, danger }) => (
              <Popconfirm
                key={action}
                title={`${label} абонемент?`}
                okText="Так"
                cancelText="Ні"
                onConfirm={() => onAction(membership, action)}
              >
                <Button size="small" danger={danger}>
                  {label}
                </Button>
              </Popconfirm>
            ))}
          </Flex>
        </Flex>
      </Flex>
    </Card>
  );
}

function VisitsTab({ clientId }) {
  const [page, setPage] = useState(1);
  const load = useCallback(
    () => fetchClientVisits(clientId, VISITS_PAGE, (page - 1) * VISITS_PAGE),
    [clientId, page],
  );
  const { data, loading } = useApi(load);
  return (
    <Table
      rowKey="id"
      size="small"
      loading={loading}
      dataSource={data?.items ?? []}
      columns={[
        {
          title: 'Дата й час',
          dataIndex: 'checked_in_at',
          render: (v) => clubTime(v).format('DD.MM.YYYY, HH:mm'),
        },
        { title: 'Абонемент', dataIndex: 'tariff_name' },
        { title: 'Залишок після входу', dataIndex: 'visits_left', render: (v) => v ?? '∞' },
      ]}
      pagination={{
        current: page,
        pageSize: VISITS_PAGE,
        total: data?.total ?? 0,
        onChange: setPage,
        hideOnSinglePage: true,
      }}
      locale={{ emptyText: <Empty description="Відвідувань ще немає" /> }}
    />
  );
}

// Client card for the reception (Ф-1, Ф-2, Ф-5): details, memberships with state actions, visits
export default function ClientDetailPage() {
  const { clientId } = useParams();
  const id = Number(clientId);
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { message } = App.useApp();
  const [editing, setEditing] = useState(false);

  const load = useCallback(() => loadClientCard(id), [id]);
  const { data, error, loading, reload } = useApi(load);
  const selling = searchParams.get('sell') === '1';
  const setSelling = (open) => setSearchParams(open ? { sell: '1' } : {}, { replace: true });

  if (loading && !data) return <PageSpinner />;
  if (error && !data) return <LoadError error={error} onRetry={reload} />;

  const { client, memberships, bookings } = data;

  const changeState = async (membership, action) => {
    try {
      await changeMembershipState(membership.id, action);
      message.success('Стан абонемента змінено');
      reload();
    } catch (err) {
      message.error(getErrorMessage(err));
    }
  };

  const remove = async () => {
    try {
      await deleteClient(client.id);
      message.success('Клієнта видалено');
      navigate('/staff/clients', { replace: true });
    } catch (err) {
      message.error(getErrorMessage(err));
    }
  };

  return (
    <>
      <PageHeader
        title={client.full_name}
        subtitle={`${client.age} р. · ${client.phone}`}
        extra={
          <>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setSelling(true)}>
              Оформити абонемент
            </Button>
            <Button icon={<EditOutlined />} onClick={() => setEditing(true)}>
              Редагувати
            </Button>
            {user.role === ADMIN && (
              <Popconfirm
                title="Видалити клієнта?"
                description="Клієнта з абонементами видалити не можна"
                okText="Видалити"
                okButtonProps={{ danger: true }}
                cancelText="Ні"
                onConfirm={remove}
              >
                <Button danger icon={<DeleteOutlined />} aria-label="Видалити клієнта" />
              </Popconfirm>
            )}
          </>
        }
      />

      <Card className="soft-card" style={{ marginBottom: 24 }}>
        <Descriptions column={{ xs: 1, sm: 2, lg: 3 }} size="small">
          <Descriptions.Item label="Дата народження">
            {dayjs(client.birth_date).format(DATE)}
          </Descriptions.Item>
          <Descriptions.Item label="Email">{client.email}</Descriptions.Item>
          <Descriptions.Item label="Сповіщення">
            <Tag>{CHANNEL_LABELS[client.notification_channel]}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Клієнт з">
            {dayjs(client.created_at).format(DATE)}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Tabs
        items={[
          {
            key: 'memberships',
            label: `Абонементи (${memberships.length})`,
            children: memberships.length ? (
              <Flex vertical gap={12}>
                {memberships.map((m) => (
                  <MembershipItem key={m.id} membership={m} onAction={changeState} />
                ))}
              </Flex>
            ) : (
              <Empty description="Абонементів ще немає" />
            ),
          },
          { key: 'visits', label: 'Відвідування', children: <VisitsTab clientId={client.id} /> },
          {
            key: 'bookings',
            label: `Записи (${bookings.length})`,
            children: bookings.length ? (
              <Flex vertical gap={12}>
                {bookings.map((b) => (
                  <SessionRow
                    key={b.id}
                    session={b.session}
                    showPlaces={false}
                    extra={
                      <Flex gap={8} align="center">
                        <Text type="secondary">
                          {clubTime(b.session.start_at).format('dd, D MMM')}
                        </Text>
                        <BookingStatusTag status={b.status} />
                      </Flex>
                    }
                  />
                ))}
              </Flex>
            ) : (
              <Empty description="Майбутніх записів немає" />
            ),
          },
        ]}
      />

      <ClientFormDrawer
        client={client}
        open={editing}
        onClose={() => setEditing(false)}
        onSaved={() => {
          setEditing(false);
          message.success('Дані клієнта збережено');
          reload();
        }}
      />
      <SellMembershipModal
        clientId={client.id}
        open={selling}
        onClose={() => setSelling(false)}
        onSold={(membership) => {
          setSelling(false);
          message.success(`Абонемент «${membership.tariff.name}» оформлено`);
          reload();
        }}
      />
    </>
  );
}
