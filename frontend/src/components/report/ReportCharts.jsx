import { Card, Col, Row } from 'antd';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { formatMoney } from '../../utils/format';
import { findTable, periodLabel } from './reportUtils';

const ORANGE = '#ff6b35';
const ACTIVITY = [
  { key: 'активний', color: '#52c41a' },
  { key: 'помірний', color: '#faad14' },
  { key: 'неактивний', color: '#bfbfbf' },
];

function ChartCard({ title, children, span = 12 }) {
  return (
    <Col xs={24} lg={span}>
      <Card className="soft-card" title={title} style={{ height: '100%' }}>
        <ResponsiveContainer width="100%" height={260}>
          {children}
        </ResponsiveContainer>
      </Card>
    </Col>
  );
}

function IncomeCharts({ report }) {
  const byTariff = findTable(report, 'tariff')?.rows ?? [];
  const byPeriod = findTable(report, 'period')?.rows ?? [];
  return (
    <>
      <ChartCard title="Виручка по днях / місяцях" span={14}>
        <AreaChart data={byPeriod.map((r) => ({ ...r, revenue: Number(r.revenue) }))}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="period" tickFormatter={periodLabel} fontSize={12} minTickGap={12} />
          <YAxis fontSize={12} width={64} />
          <Tooltip formatter={(v) => [formatMoney(v), 'Виручка']} labelFormatter={periodLabel} />
          <Area dataKey="revenue" stroke={ORANGE} fill={ORANGE} fillOpacity={0.2} />
        </AreaChart>
      </ChartCard>
      <ChartCard title="Виручка за тарифами" span={10}>
        <BarChart
          data={byTariff.map((r) => ({ ...r, revenue: Number(r.revenue) }))}
          layout="vertical"
          margin={{ left: 24 }}
        >
          <XAxis type="number" fontSize={12} />
          <YAxis type="category" dataKey="tariff" width={140} fontSize={12} />
          <Tooltip formatter={(v) => [formatMoney(v), 'Виручка']} />
          <Bar dataKey="revenue" fill={ORANGE} radius={[0, 6, 6, 0]} />
        </BarChart>
      </ChartCard>
    </>
  );
}

function LoadCharts({ report }) {
  const trainers = findTable(report, 'trainer')?.rows ?? [];
  return (
    <ChartCard title="Заповненість занять тренерів, %" span={24}>
      {/* not `fill`: Recharts treats a data field named `fill` as the bar colour */}
      <BarChart data={trainers.map((r) => ({ trainer: r.trainer, percent: Number(r.fill) }))}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="trainer" fontSize={12} />
        <YAxis domain={[0, 100]} fontSize={12} />
        <Tooltip formatter={(v) => [`${v}%`, 'Заповненість']} />
        <Bar dataKey="percent" fill={ORANGE} radius={[6, 6, 0, 0]} />
      </BarChart>
    </ChartCard>
  );
}

function ActivityChart({ report }) {
  const rows = findTable(report, 'activity')?.rows ?? [];
  const data = ACTIVITY.map((a) => ({
    ...a,
    clients: rows.filter((r) => r.activity === a.key).length,
  }));
  return (
    <ChartCard title="Клієнти за активністю" span={12}>
      <BarChart data={data}>
        <XAxis dataKey="key" fontSize={12} />
        <YAxis allowDecimals={false} fontSize={12} />
        <Tooltip formatter={(v) => [v, 'Клієнтів']} />
        <Bar dataKey="clients" radius={[6, 6, 0, 0]}>
          {data.map((d) => (
            <Cell key={d.key} fill={d.color} />
          ))}
        </Bar>
      </BarChart>
    </ChartCard>
  );
}

const CHARTS = { income: IncomeCharts, load: LoadCharts, 'client-activity': ActivityChart };

// Charts above the tables; which ones depends on the report
export default function ReportCharts({ report }) {
  const Charts = CHARTS[report.code];
  if (!Charts) return null;
  return (
    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
      <Charts report={report} />
    </Row>
  );
}
