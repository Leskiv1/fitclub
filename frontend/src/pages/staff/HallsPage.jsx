import { Form, Input, InputNumber } from 'antd';
import { fetchHalls, hallsApi } from '../../api/catalog';
import PageHeader from '../../components/PageHeader';
import CrudTable from '../../components/staff/CrudTable';

const columns = [
  { title: 'Назва', dataIndex: 'name' },
  { title: 'Місткість, осіб', dataIndex: 'capacity', width: 160 },
];

// ЗВ-7: halls; the capacity limits group sessions held in a hall
export default function HallsPage() {
  return (
    <>
      <PageHeader title="Зали" subtitle="Місткість залу обмежує групові заняття в ньому" />
      <CrudTable
        load={fetchHalls}
        save={hallsApi.save}
        remove={hallsApi.remove}
        columns={columns}
        addLabel="Додати зал"
        entityName="зал"
        renderForm={() => (
          <>
            <Form.Item
              name="name"
              label="Назва"
              rules={[{ required: true, min: 2, max: 100, message: 'Від 2 до 100 символів' }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              name="capacity"
              label="Місткість, осіб"
              rules={[{ required: true, message: 'Вкажіть місткість' }]}
            >
              <InputNumber min={1} max={1000} style={{ width: '100%' }} />
            </Form.Item>
          </>
        )}
      />
    </>
  );
}
