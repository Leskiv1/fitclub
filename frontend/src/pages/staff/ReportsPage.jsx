import { useCallback, useState } from 'react';
import { FileExcelOutlined, FilePdfOutlined } from '@ant-design/icons';
import { App, Button, DatePicker, Flex, Segmented, Tabs, Typography } from 'antd';
import { downloadReport, fetchReport } from '../../api/admin';
import LoadError from '../../components/LoadError';
import PageHeader from '../../components/PageHeader';
import PageSpinner from '../../components/PageSpinner';
import ReportCharts from '../../components/report/ReportCharts';
import ReportSection from '../../components/report/ReportSection';
import useApi from '../../hooks/useApi';
import { clubTime, dayjs, ISO_DATE, weekStart } from '../../utils/dates';
import { getErrorMessage } from '../../utils/errors';

const { Text, Title } = Typography;

const rangeParams = ([start, end]) => ({
  start: start.format(ISO_DATE),
  end: end.format(ISO_DATE),
});

// Period filter of each report -> query parameters of /api/reports/{code}
function ActivityFilter({ onChange }) {
  const [range, setRange] = useState([dayjs().subtract(29, 'day'), dayjs()]);
  return (
    <DatePicker.RangePicker
      format="DD.MM.YYYY"
      value={range}
      allowClear={false}
      onChange={(r) => {
        setRange(r);
        onChange(rangeParams(r));
      }}
    />
  );
}

function LoadFilter({ onChange }) {
  const monday = weekStart(dayjs());
  const [range, setRange] = useState([monday, monday.add(6, 'day')]);
  return (
    <DatePicker.RangePicker
      format="DD.MM.YYYY"
      value={range}
      allowClear={false}
      onChange={(r) => {
        setRange(r);
        onChange(rangeParams(r));
      }}
    />
  );
}

function IncomeFilter({ onChange }) {
  const [mode, setMode] = useState('month');
  const [value, setValue] = useState(dayjs());
  const emit = (m, v) =>
    onChange(m === 'month' ? { year: v.year(), month: v.month() + 1 } : { year: v.year() });
  return (
    <Flex gap={8} wrap>
      <Segmented
        value={mode}
        onChange={(m) => {
          setMode(m);
          emit(m, value);
        }}
        options={[
          { value: 'month', label: 'Місяць' },
          { value: 'year', label: 'Рік' },
        ]}
      />
      <DatePicker
        picker={mode}
        value={value}
        allowClear={false}
        format={mode === 'month' ? 'MMMM YYYY' : 'YYYY'}
        onChange={(v) => {
          setValue(v);
          emit(mode, v);
        }}
      />
    </Flex>
  );
}

const REPORTS = [
  { code: 'client-activity', label: 'З-1. Активність клієнтів', Filter: ActivityFilter },
  { code: 'income', label: 'З-2. Доходи', Filter: IncomeFilter },
  { code: 'load', label: 'З-3. Завантаженість', Filter: LoadFilter },
];

function ReportPanel({ code, Filter }) {
  const { message } = App.useApp();
  const [params, setParams] = useState({}); // empty -> the server's default period
  const [exporting, setExporting] = useState(null);

  const key = JSON.stringify(params);
  const load = useCallback(() => fetchReport(code, JSON.parse(key)), [code, key]);
  const { data: report, error, loading, reload } = useApi(load);

  // Strategy on the server: the same report tree, a different exporter per format
  const exportAs = async (format) => {
    setExporting(format);
    try {
      await downloadReport(code, params, format);
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setExporting(null);
    }
  };

  return (
    <>
      <Flex justify="space-between" align="center" gap={12} wrap style={{ marginBottom: 16 }}>
        <Filter onChange={setParams} />
        <Flex gap={8}>
          <Button
            icon={<FileExcelOutlined />}
            loading={exporting === 'csv'}
            onClick={() => exportAs('csv')}
          >
            CSV
          </Button>
          <Button
            icon={<FilePdfOutlined />}
            loading={exporting === 'pdf'}
            onClick={() => exportAs('pdf')}
          >
            PDF
          </Button>
        </Flex>
      </Flex>
      {error && !report && <LoadError error={error} onRetry={reload} />}
      {loading && !report && <PageSpinner />}
      {report && (
        <div style={{ opacity: loading ? 0.6 : 1 }}>
          <Title level={4} style={{ marginBottom: 0 }}>
            {report.title}
          </Title>
          <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
            Період: {report.period} · сформовано{' '}
            {clubTime(report.generated_at).format('DD.MM.YYYY HH:mm')}
          </Text>
          <ReportCharts report={report} />
          {report.sections.map((section, i) => (
            <ReportSection key={`${section.title}-${i}`} section={section} />
          ))}
        </div>
      )}
    </>
  );
}

// З-1, З-2, З-3: reports with charts and CSV/PDF export (admin)
export default function ReportsPage() {
  return (
    <>
      <PageHeader
        title="Звіти"
        subtitle="Клієнти й активність, доходи, завантаженість тренерів і залів"
      />
      <Tabs
        destroyOnHidden
        items={REPORTS.map(({ code, label, Filter }) => ({
          key: code,
          label,
          children: <ReportPanel code={code} Filter={Filter} />,
        }))}
      />
    </>
  );
}
