import { dayjs } from '../../utils/dates';
import { formatMoney } from '../../utils/format';

// A report is a tree of sections (Composite on the server): group -> [summary | table | group]

// All leaf sections in document order
export function flattenSections(sections) {
  return sections.flatMap((s) => (s.type === 'group' ? flattenSections(s.sections ?? []) : [s]));
}

// The first table that has a column with this key
export const findTable = (report, columnKey) =>
  flattenSections(report.sections).find(
    (s) => s.type === 'table' && s.columns.some((c) => c.key === columnKey),
  );

export const summaryItems = (report) =>
  flattenSections(report.sections).find((s) => s.type === 'summary')?.items ?? [];

const number = new Intl.NumberFormat('uk-UA', { maximumFractionDigits: 1 });

// Cell formatting by the column's kind — the same kinds the CSV/PDF exporters use
const FORMATTERS = {
  money: (v) => formatMoney(v),
  percent: (v) => `${number.format(Number(v))}%`,
  number: (v) => number.format(Number(v)),
  int: (v) => String(v),
  // "2026-11-06" (day) or "2026-11" (month in a yearly income report)
  date: (v) =>
    /^\d{4}-\d{2}$/.test(v) ? dayjs(`${v}-01`).format('MMM YYYY') : dayjs(v).format('DD.MM.YYYY'),
  text: (v) => String(v),
};

export function formatValue(value, kind) {
  if (value === null || value === undefined || value === '') return '—';
  return (FORMATTERS[kind] ?? FORMATTERS.text)(value);
}

// Short axis label for a period cell
export const periodLabel = (v) =>
  /^\d{4}-\d{2}$/.test(v) ? dayjs(`${v}-01`).format('MMM') : dayjs(v).format('D.MM');
