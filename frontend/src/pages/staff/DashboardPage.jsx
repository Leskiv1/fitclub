import { AlertOutlined, LoginOutlined, TeamOutlined, WalletOutlined } from '@ant-design/icons';
import { Card, Col, Empty, Flex, Row, Table, Tag, Typography } from 'antd';
import { Link } from 'react-router-dom';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { fetchReport } from '../../api/admin';
import { fetchSettings } from '../../api/catalog';
import { fetchDailyVisits, fetchTodayVisits } from '../../api/checkIns';
import LoadError from '../../components/LoadError';
import PageHeader from '../../components/PageHeader';
import PageSpinner from '../../components/PageSpinner';
import { findTable, periodLabel, summaryItems } from '../../components/report/reportUtils';
import useApi from '../../hooks/useApi';
import { dayjs, ISO_DATE } from '../../utils/dates';
import { days, formatMoney, visits } from '../../utils/format';

const { Text } = Typography;
const ORANGE = '#ff6b35';

// The dashboard reuses the reports (Proxy caches them) plus today's check-ins and daily traffic
async function loadDashboard() {
  const [activity, income, today, daily, settings] = await Promise.all([
    fetchReport('client-activity'),
    fetchReport('income'),
    fetchTodayVisits(),
    fetchDailyVisits(14),
    fetchSettings(),
  ]);
  const clients = findTable(activity, 'activity')?.rows ?? [];
  const todayIso = dayjs().format(ISO_DATE);
  const lastWarned = dayjs().add(settings.expiry_warning_days, 'day').format(ISO_DATE);
  return {
    activeClients: clients.filter((c) => c.status === 'active').length,
    visitsToday: today.length,
    revenue: summaryItems(income).find((i) => i.kind === 'money')?.value ?? 0,
    incomePeriod: income.period,
    incomeByDay: (findTable(income, 'period')?.rows ?? []).map((r) => ({
      ...r,
      revenue: Number(r.revenue),
    })),
    daily,
    warningDays: settings.expiry_warning_days,
    expiring: clients
      .filter(
        (c) => c.status === 'active' && c.valid_until >= todayIso && c.valid_until <= lastWarned,
      )
      .sort((a, b) => a.valid_until.localeCompare(b.valid_until)),
  };
}

function Kpi({ icon, label, value, hint }) {
  return (
    <Col xs={12} lg={6}>
      <Card className="soft-card kpi">
        <Flex justify="space-between" align="start">
          <span className="kpi__label">{label}</span>
          <span style={{ color: ORANGE, fontSize: 20 }}>{icon}</span>
        </Flex>
        <span className="kpi__value">{value}</span>
        {hint && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            {hint}
          </Text>
        )}
      </Card>
    </Col>
  );
}

const expiringColumns = [
  {
    title: 'Клієнт',
    dataIndex: 'full_name',
    render: (name, c) => <Link to={`/staff/clients?q=${encodeURIComponent(c.phone)}`}>{name}</Link>,
  },
  { title: 'Телефон', dataIndex: 'phone', responsive: ['md'] },
  { title: 'Абонемент', dataIndex: 'tariff', responsive: ['lg'] },
  {
    title: 'Дійсний до',
    dataIndex: 'valid_until',
    render: (d) => {
      const left = dayjs(d).diff(dayjs().startOf('day'), 'day');
      return (
        <Flex gap={8} align="center" wrap>
          {dayjs(d).format('DD.MM.YYYY')}
          <Tag color={left <= 1 ? 'red' : 'orange'}>{left === 0 ? 'сьогодні' : days(left)}</Tag>
        </Flex>
      );
    },
  },
];

// Admin dashboard: KPI, revenue of the month, traffic by day, memberships that end soon
export default function DashboardPage() {
  const { data, error, loading, reload } = useApi(loadDashboard);

  if (error && !data) return <LoadError error={error} onRetry={reload} />;
  if (loading && !data) return <PageSpinner />;

  return (
    <>
      <PageHeader title="Дашборд" subtitle={`Показники клубу · ${data.incomePeriod}`} />
      <Row gutter={[16, 16]}>
        <Kpi icon={<TeamOutlined />} label="Активні клієнти" value={data.activeClients} />
        <Kpi icon={<LoginOutlined />} label="Відвідування сьогодні" value={data.visitsToday} />
        <Kpi icon={<WalletOutlined />} label="Дохід за місяць" value={formatMoney(data.revenue)} />
        <Kpi
          icon={<AlertOutlined />}
          label="Абонементи закінчуються"
          value={data.expiring.length}
          hint={`протягом ${days(data.warningDays)}`}
        />
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card className="soft-card" title="Дохід за місяць по днях" style={{ height: '100%' }}>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={data.incomeByDay}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="period" tickFormatter={periodLabel} fontSize={12} minTickGap={12} />
                <YAxis fontSize={12} width={64} />
                <Tooltip
                  formatter={(v) => [formatMoney(v), 'Виручка']}
                  labelFormatter={periodLabel}
                />
                <Area dataKey="revenue" stroke={ORANGE} fill={ORANGE} fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card className="soft-card" title="Трафік по днях (14 днів)" style={{ height: '100%' }}>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data.daily}>
                <XAxis
                  dataKey="date"
                  tickFormatter={(d) => dayjs(d).format('dd')}
                  fontSize={12}
                  interval={0}
                />
                <YAxis allowDecimals={false} fontSize={12} width={32} />
                <Tooltip
                  formatter={(v) => [visits(v), 'Прийшли']}
                  labelFormatter={(d) => dayjs(d).format('dd, D MMMM')}
                />
                <Bar dataKey="visits" fill={ORANGE} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Card
        className="soft-card"
        style={{ marginTop: 16 }}
        title={`Абонементи, що закінчуються (${data.expiring.length})`}
      >
        <Table
          rowKey="phone"
          size="small"
          columns={expiringColumns}
          dataSource={data.expiring}
          pagination={{ pageSize: 8, hideOnSinglePage: true }}
          locale={{
            emptyText: (
              <Empty description={`Найближчі ${days(data.warningDays)} нічого не закінчується`} />
            ),
          }}
        />
      </Card>
    </>
  );
}
