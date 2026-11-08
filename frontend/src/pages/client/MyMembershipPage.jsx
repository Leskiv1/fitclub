import { useCallback } from 'react';
import { PlusOutlined, RightOutlined, WarningOutlined } from '@ant-design/icons';
import { Alert, Button, Card, Col, Empty, Flex, Progress, Row, Tag, Typography } from 'antd';
import { Link } from 'react-router-dom';
import { fetchClientBookings } from '../../api/bookings';
import { fetchSettings, fetchTariffs } from '../../api/catalog';
import { fetchClient, fetchClientVisits } from '../../api/clients';
import { fetchClientMemberships } from '../../api/memberships';
import useAuth from '../../auth/useAuth';
import LoadError from '../../components/LoadError';
import PageSpinner from '../../components/PageSpinner';
import SessionRow from '../../components/SessionRow';
import { MembershipStatusTag } from '../../components/StatusTag';
import VisitsChart from '../../components/VisitsChart';
import useApi from '../../hooks/useApi';
import { clubTime, dayjs, ISO_DATE } from '../../utils/dates';
import { daysLeftLabel, formatMoney, TARIFF_TYPE_LABELS, visits } from '../../utils/format';

const { Title, Text } = Typography;
const DATE = 'DD.MM.YYYY';
const LOW_VISITS = 2;

async function loadCabinet(clientId) {
  const [client, memberships, tariffs, settings, bookings, visitPage] = await Promise.all([
    fetchClient(clientId),
    fetchClientMemberships(clientId),
    fetchTariffs(),
    fetchSettings(),
    fetchClientBookings(clientId, true),
    fetchClientVisits(clientId, 100),
  ]);
  // The server decides which membership is current (client card); a renewal starts after it
  const current = memberships.find((m) => m.id === client.membership?.id) ?? null;
  const today = dayjs().format(ISO_DATE);
  const next =
    memberships.find(
      (m) => m.id !== current?.id && m.status === 'active' && m.start_date > today,
    ) ?? null;
  return {
    current,
    next,
    history: memberships.filter((m) => m.id !== current?.id && m.id !== next?.id),
    tariff: tariffs.find((t) => t.id === current?.tariff.id) ?? null,
    warningDays: settings.expiry_warning_days,
    upcoming: bookings.filter((b) => b.status === 'booked').slice(0, 3),
    visits: visitPage.items,
    visitsTotal: visitPage.total,
  };
}

function ExpiryBanner({ membership, warningDays }) {
  const endsSoon = membership.status === 'active' && membership.days_left <= warningDays;
  const fewVisits = membership.visits_left !== null && membership.visits_left <= LOW_VISITS;
  if (!endsSoon && !fewVisits) return null;

  const title = endsSoon
    ? daysLeftLabel(membership)
    : `Залишилось ${visits(membership.visits_left)}`;
  return (
    <Alert
      type="warning"
      showIcon
      icon={<WarningOutlined />}
      title={title}
      description={`Абонемент діє до ${dayjs(membership.end_date).format(DATE)}. Новий почнеться одразу після поточного.`}
      action={
        <Link to={`/my/purchase?tariff=${membership.tariff.id}`}>
          <Button type="primary">Продовжити</Button>
        </Link>
      }
      style={{ marginBottom: 16, flexWrap: 'wrap', gap: 8 }}
    />
  );
}

function MembershipCard({ membership, tariff }) {
  const start = dayjs(membership.start_date);
  const end = dayjs(membership.end_date);
  const totalDays = end.diff(start, 'day') + 1;
  const started = !start.isAfter(dayjs(), 'day');
  const usedPercent = started
    ? Math.round(((totalDays - membership.days_left) / totalDays) * 100)
    : 0;
  const limit = tariff?.visit_limit;

  return (
    <div className="membership-card">
      <Flex justify="space-between" align="start" gap={8}>
        <div>
          <Text className="membership-card__muted">
            {TARIFF_TYPE_LABELS[membership.tariff.type]}
          </Text>
          <Title level={3} style={{ margin: 0 }}>
            {membership.tariff.name}
          </Title>
        </div>
        <MembershipStatusTag status={membership.status} />
      </Flex>

      <Flex vertical gap={4} style={{ marginTop: 24 }}>
        <Flex justify="space-between" wrap gap={8}>
          <div>
            <Text className="membership-card__muted">Термін дії</Text>
            <Title level={5} style={{ margin: 0 }}>
              {start.format(DATE)} – {end.format(DATE)}
            </Title>
          </div>
          <Text>{daysLeftLabel(membership)}</Text>
        </Flex>
        <Progress
          percent={usedPercent}
          showInfo={false}
          strokeColor="#ff6b35"
          railColor="#43474e"
        />
      </Flex>

      {limit && (
        <Flex vertical gap={4} style={{ marginTop: 12 }}>
          <Text>
            Відвідувань залишилось: {membership.visits_left} з {limit}
          </Text>
          <Progress
            percent={Math.round((membership.visits_left / limit) * 100)}
            showInfo={false}
            strokeColor="#7bd0ff"
            railColor="#43474e"
          />
        </Flex>
      )}

      {membership.options.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <Text className="membership-card__muted">Включені опції</Text>
          <Flex gap={8} wrap style={{ marginTop: 8 }}>
            {membership.options.map((o) => (
              <Tag key={o.id} variant="filled">
                {o.name}
              </Tag>
            ))}
          </Flex>
        </div>
      )}

      <Text className="membership-card__muted" style={{ display: 'block', marginTop: 16 }}>
        Сплачено {formatMoney(membership.total_price)}
        {Number(membership.discount_amount) > 0 &&
          ` · знижка ${formatMoney(membership.discount_amount)}`}
      </Text>
    </div>
  );
}

// "Мій абонемент": current membership, expiry banner (Ф-6), nearest bookings, visit history (Ф-2)
export default function MyMembershipPage() {
  const { user } = useAuth();
  const load = useCallback(() => loadCabinet(user.client_id), [user.client_id]);
  const { data, error, loading, reload } = useApi(load);

  if (loading && !data) return <PageSpinner />;
  if (error && !data) return <LoadError error={error} onRetry={reload} />;

  const { current, next, history, tariff, warningDays, upcoming } = data;
  const monthAgo = dayjs().subtract(30, 'day').format(ISO_DATE);
  const lastMonth = data.visits.filter((v) => v.visit_date >= monthAgo).length;

  return (
    <>
      <Title level={2} className="page-title">
        Мій абонемент
      </Title>
      <Text className="page-subtitle">Вітаємо, {user.full_name}!</Text>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={14}>
          {current ? (
            <>
              {!next && <ExpiryBanner membership={current} warningDays={warningDays} />}
              <MembershipCard membership={current} tariff={tariff} />
              {next && (
                <Alert
                  type="info"
                  showIcon
                  style={{ marginTop: 16 }}
                  title={`Наступний абонемент «${next.tariff.name}» діє з ${dayjs(next.start_date).format(DATE)}`}
                />
              )}
            </>
          ) : (
            <Card className="soft-card">
              <Empty description="У вас немає абонемента, що діє сьогодні">
                <Link to="/my/purchase">
                  <Button type="primary">Оформити абонемент</Button>
                </Link>
              </Empty>
            </Card>
          )}

          <Card className="soft-card" style={{ marginTop: 24 }}>
            <Flex justify="space-between" align="baseline" wrap>
              <Title level={4} style={{ margin: 0 }}>
                Графік відвідувань
              </Title>
              <Text type="secondary">усього {visits(data.visitsTotal)}</Text>
            </Flex>
            <Text>
              За останні 30 днів: <Text strong>{visits(lastMonth)}</Text>
            </Text>
            <VisitsChart visits={data.visits} />
            {data.visits.length > 0 && (
              <Flex vertical gap={4} style={{ marginTop: 8 }}>
                <Text strong>Останні відвідування</Text>
                {data.visits.slice(0, 5).map((v) => (
                  <Flex key={v.id} justify="space-between">
                    <Text>{clubTime(v.checked_in_at).format('D MMMM, HH:mm')}</Text>
                    <Text type="secondary">{v.tariff_name}</Text>
                  </Flex>
                ))}
              </Flex>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={10}>
          <Flex justify="space-between" align="baseline">
            <Title level={4}>Найближчі заняття</Title>
            <Link to="/my/bookings">
              Усі записи <RightOutlined />
            </Link>
          </Flex>
          <Flex vertical gap={12}>
            {upcoming.length ? (
              upcoming.map((b) => (
                <SessionRow
                  key={b.id}
                  session={b.session}
                  showPlaces={false}
                  extra={
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {clubTime(b.session.start_at).format('dd, D MMM')}
                    </Text>
                  }
                />
              ))
            ) : (
              <Text type="secondary">Ви ще не записані на заняття</Text>
            )}
            <Link to="/my/schedule">
              <Card className="soft-card" hoverable>
                <Flex align="center" gap={16}>
                  <Button type="primary" shape="circle" icon={<PlusOutlined />} tabIndex={-1} />
                  <Flex vertical style={{ flex: 1 }}>
                    <Text strong>Записатися на тренування</Text>
                    <Text type="secondary">Групові програми цього тижня</Text>
                  </Flex>
                  <RightOutlined />
                </Flex>
              </Card>
            </Link>
          </Flex>

          {history.length > 0 && (
            <Card className="soft-card" style={{ marginTop: 24 }} title="Історія абонементів">
              <Flex vertical gap={12}>
                {history.map((m) => (
                  <Flex key={m.id} justify="space-between" align="center" gap={8}>
                    <Flex vertical>
                      <Text strong>{m.tariff.name}</Text>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {dayjs(m.start_date).format(DATE)} – {dayjs(m.end_date).format(DATE)}
                      </Text>
                    </Flex>
                    <MembershipStatusTag status={m.status} />
                  </Flex>
                ))}
              </Flex>
            </Card>
          )}
        </Col>
      </Row>
    </>
  );
}
