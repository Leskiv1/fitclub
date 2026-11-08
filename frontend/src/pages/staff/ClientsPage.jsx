import { useCallback, useState } from 'react';
import { UserAddOutlined } from '@ant-design/icons';
import { Button, Input, Table } from 'antd';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { searchClients } from '../../api/clients';
import LoadError from '../../components/LoadError';
import PageHeader from '../../components/PageHeader';
import { MembershipStatusTag } from '../../components/StatusTag';
import ClientFormDrawer from '../../components/staff/ClientFormDrawer';
import useApi from '../../hooks/useApi';
import { dayjs } from '../../utils/dates';

const PAGE_SIZE = 20;

const columns = [
  {
    title: 'ПІБ',
    dataIndex: 'full_name',
    render: (name, c) => <Link to={`/staff/clients/${c.id}`}>{name}</Link>,
  },
  { title: 'Вік', dataIndex: 'age', width: 70, responsive: ['md'] },
  { title: 'Телефон', dataIndex: 'phone', responsive: ['sm'] },
  {
    title: 'Абонемент',
    dataIndex: ['membership', 'tariff_name'],
    responsive: ['lg'],
    render: (v) => v ?? '—',
  },
  {
    title: 'Статус',
    dataIndex: ['membership', 'status'],
    render: (status) => (status ? <MembershipStatusTag status={status} /> : '—'),
  },
  {
    title: 'Дійсний до',
    dataIndex: ['membership', 'end_date'],
    responsive: ['md'],
    render: (d) => (d ? dayjs(d).format('DD.MM.YYYY') : '—'),
  },
];

// Ф-1: client registry — name, age, phone, membership and its validity, search and paging
export default function ClientsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [query, setQuery] = useState(() => searchParams.get('q') ?? '');
  const [page, setPage] = useState(1);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const load = useCallback(
    () => searchClients({ q: query, offset: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE }),
    [query, page],
  );
  const { data, error, loading, reload } = useApi(load);

  const onSaved = (client, { sell }) => {
    setDrawerOpen(false);
    navigate(`/staff/clients/${client.id}${sell ? '?sell=1' : ''}`);
  };

  return (
    <>
      <PageHeader
        title="Клієнти"
        subtitle={data ? `Усього: ${data.total}` : 'База клієнтів клубу'}
        extra={
          <Button type="primary" icon={<UserAddOutlined />} onClick={() => setDrawerOpen(true)}>
            Новий клієнт
          </Button>
        }
      />
      <Input.Search
        defaultValue={query}
        placeholder="Пошук за ПІБ або телефоном"
        allowClear
        enterButton="Знайти"
        size="large"
        onSearch={(value) => {
          setQuery(value.trim());
          setPage(1);
        }}
        style={{ maxWidth: 480, marginBottom: 16 }}
      />
      {error && !data ? (
        <LoadError error={error} onRetry={reload} />
      ) : (
        <Table
          rowKey="id"
          columns={columns}
          dataSource={data?.items ?? []}
          loading={loading}
          onRow={(c) => ({ onDoubleClick: () => navigate(`/staff/clients/${c.id}`) })}
          pagination={{
            current: page,
            pageSize: PAGE_SIZE,
            total: data?.total ?? 0,
            onChange: setPage,
            showSizeChanger: false,
          }}
        />
      )}
      <ClientFormDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} onSaved={onSaved} />
    </>
  );
}
