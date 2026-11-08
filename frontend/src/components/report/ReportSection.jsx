import { Card, Col, Flex, Row, Table, Tag, Typography } from 'antd';
import { MembershipStatusTag } from '../StatusTag';
import { formatValue } from './reportUtils';

const { Title, Text } = Typography;

const ACTIVITY_COLORS = { активний: 'green', помірний: 'gold', неактивний: 'default' };

// Hall load by weekday (З-3): the cell colour grows with the percentage
const isHeatCell = (column) => column.kind === 'percent' && /^d\d$/.test(column.key);
const heat = (value) => ({
  style: { background: `rgba(255, 107, 53, ${Math.min(Number(value) || 0, 100) / 100})` },
  className: 'heatmap__cell',
});

function renderCell(column, value) {
  if (column.key === 'status' && value) return <MembershipStatusTag status={value} />;
  if (column.key === 'activity') return <Tag color={ACTIVITY_COLORS[value]}>{value}</Tag>;
  return formatValue(value, column.kind);
}

function SummarySection({ section }) {
  return (
    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
      {section.items.map((item) => (
        <Col key={item.label} xs={12} md={8} lg={6}>
          <Card size="small" className="soft-card" style={{ height: '100%' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {item.label}
            </Text>
            <div style={{ fontSize: 22, fontWeight: 800 }}>
              {formatValue(item.value, item.kind)}
            </div>
          </Card>
        </Col>
      ))}
    </Row>
  );
}

function TableSection({ section }) {
  const columns = section.columns.map((column) => ({
    title: column.label,
    dataIndex: column.key,
    align: ['money', 'percent', 'number', 'int'].includes(column.kind) ? 'right' : 'left',
    render: (value) => renderCell(column, value),
    onCell: isHeatCell(column) ? (row) => heat(row[column.key]) : undefined,
  }));
  return (
    <Card className="soft-card heatmap" title={section.title} style={{ marginBottom: 24 }}>
      <Table
        rowKey="__row"
        size="small"
        columns={columns}
        dataSource={section.rows.map((row, i) => ({ ...row, __row: i }))}
        scroll={{ x: 'max-content' }}
        pagination={{ pageSize: 15, hideOnSinglePage: true }}
        summary={
          section.totals
            ? () => (
                <Table.Summary.Row>
                  {section.columns.map((column, i) => (
                    <Table.Summary.Cell key={column.key} index={i} align={columns[i].align}>
                      <Text strong>
                        {i === 0 && section.totals[column.key] === undefined
                          ? 'Разом'
                          : formatValue(section.totals[column.key], column.kind)}
                      </Text>
                    </Table.Summary.Cell>
                  ))}
                </Table.Summary.Row>
              )
            : undefined
        }
      />
    </Card>
  );
}

// Renders any section of the report tree — the client-side twin of the server's exporters
export default function ReportSection({ section }) {
  if (section.type === 'summary') return <SummarySection section={section} />;
  if (section.type === 'table') return <TableSection section={section} />;
  return (
    <Flex vertical>
      <Title level={4}>{section.title}</Title>
      {(section.sections ?? []).map((child, i) => (
        <ReportSection key={`${child.title}-${i}`} section={child} />
      ))}
    </Flex>
  );
}
