import { useCallback, useState } from 'react';
import { CheckCircleFilled, CloseCircleFilled, LoginOutlined } from '@ant-design/icons';
import { Alert, Button, Card, Col, Descriptions, Empty, Flex, Row, Table, Typography } from 'antd';
import { Link } from 'react-router-dom';
import { checkIn, fetchTodayVisits } from '../../api/checkIns';
import { fetchClient, fetchClientVisits } from '../../api/clients';
import ClientSearchSelect from '../../components/ClientSearchSelect';
import PageHeader from '../../components/PageHeader';
import PageSpinner from '../../components/PageSpinner';
import { MembershipStatusTag } from '../../components/StatusTag';
import useApi from '../../hooks/useApi';
import { clubTime, dayjs } from '../../utils/dates';
import { getErrorMessage } from '../../utils/errors';

const { Text, Title } = Typography;

async function loadCard(clientId) {
  const [client, visits] = await Promise.all([
    fetchClient(clientId),
    fetchClientVisits(clientId, 1),
  ]);
  return { client, lastVisit: visits.items[0] ?? null };
}

function ClientCard({ client, lastVisit }) {
  const m = client.membership;
  return (
    <Card className="soft-card" style={{ marginTop: 16 }}>
      <Flex justify="space-between" align="start" gap={8} wrap>
        <div>
          <Title level={4} style={{ margin: 0 }}>
            <Link to={`/staff/clients/${client.id}`}>{client.full_name}</Link>
          </Title>
          <Text type="secondary">
            {client.phone} · {client.age} р.
          </Text>
        </div>
        {m && <MembershipStatusTag status={m.status} />}
      </Flex>
      {m ? (
        <Descriptions column={{ xs: 1, sm: 2 }} size="small" style={{ marginTop: 16 }}>
          <Descriptions.Item label="Абонемент">{m.tariff_name}</Descriptions.Item>
          <Descriptions.Item label="Дійсний до">
            {dayjs(m.end_date).format('DD.MM.YYYY')}
          </Descriptions.Item>
          <Descriptions.Item label="Залишок відвідувань">
            {m.visits_left ?? 'безліміт'}
          </Descriptions.Item>
          <Descriptions.Item label="Останній візит">
            {lastVisit
              ? clubTime(lastVisit.checked_in_at).format('DD.MM.YYYY, HH:mm')
              : 'ще не було'}
          </Descriptions.Item>
        </Descriptions>
      ) : (
        <Alert
          type="warning"
          showIcon
          style={{ marginTop: 16 }}
          title="Немає абонемента, що діє сьогодні"
          action={
            <Link to={`/staff/clients/${client.id}?sell=1`}>
              <Button size="small" type="primary">
                Оформити
              </Button>
            </Link>
          }
        />
      )}
    </Card>
  );
}

function CheckInResult({ result }) {
  if (!result) return null;
  if (result.visit) {
    const left = result.visit.visits_left;
    return (
      <Alert
        type="success"
        showIcon
        icon={<CheckCircleFilled />}
        style={{ marginTop: 16 }}
        title={`Вхід дозволено о ${clubTime(result.visit.checked_in_at).format('HH:mm')}`}
        description={left === null ? 'Безлімітний абонемент' : `Залишилось відвідувань: ${left}`}
      />
    );
  }
  // Refusal from the server's Chain of Responsibility: the first failed check gives the reason
  return (
    <Alert
      type="error"
      showIcon
      icon={<CloseCircleFilled />}
      style={{ marginTop: 16 }}
      title="Вхід заборонено"
      description={getErrorMessage(result.error)}
    />
  );
}

// Ф-2: reception registers a client's arrival; the checks run on the server
export default function CheckInPage() {
  const [clientId, setClientId] = useState(null);
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const loadClient = useCallback(
    () => (clientId ? loadCard(clientId) : Promise.resolve(null)),
    [clientId],
  );
  const card = useApi(loadClient);
  const today = useApi(fetchTodayVisits);

  const choose = (id) => {
    setClientId(id);
    setResult(null);
  };

  const register = async () => {
    setSubmitting(true);
    try {
      setResult({ visit: await checkIn(clientId) });
      today.reload();
      card.reload();
    } catch (error) {
      setResult({ error });
    } finally {
      setSubmitting(false);
    }
  };

  const columns = [
    {
      title: 'Час',
      dataIndex: 'checked_in_at',
      width: 70,
      render: (v) => clubTime(v).format('HH:mm'),
    },
    {
      title: 'Клієнт',
      dataIndex: 'client_name',
      render: (name, v) => <Link to={`/staff/clients/${v.client_id}`}>{name}</Link>,
    },
    { title: 'Абонемент', dataIndex: 'tariff_name', responsive: ['md'] },
    {
      title: 'Залишок',
      dataIndex: 'visits_left',
      width: 90,
      render: (v) => v ?? '∞',
    },
  ];

  return (
    <>
      <PageHeader
        title="Реєстрація входу"
        subtitle="Знайдіть клієнта і зареєструйте відвідування"
      />
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={11}>
          <ClientSearchSelect value={clientId} onChange={choose} autoFocus />
          {clientId && card.loading && !card.data && <PageSpinner />}
          {card.error && <Alert type="error" title={getErrorMessage(card.error)} />}
          {card.data && <ClientCard {...card.data} />}
          <Button
            type="primary"
            size="large"
            block
            icon={<LoginOutlined />}
            disabled={!clientId}
            loading={submitting}
            onClick={register}
            style={{ marginTop: 16 }}
          >
            Зареєструвати вхід
          </Button>
          <CheckInResult result={result} />
        </Col>
        <Col xs={24} lg={13}>
          <Card
            className="soft-card"
            title={`Сьогодні в клубі: ${today.data?.length ?? 0}`}
            extra={<Button onClick={today.reload}>Оновити</Button>}
          >
            <Table
              rowKey="id"
              size="small"
              columns={columns}
              dataSource={today.data ?? []}
              loading={today.loading}
              pagination={{ pageSize: 10, hideOnSinglePage: true }}
              locale={{ emptyText: <Empty description="Сьогодні ще ніхто не приходив" /> }}
            />
          </Card>
        </Col>
      </Row>
    </>
  );
}
