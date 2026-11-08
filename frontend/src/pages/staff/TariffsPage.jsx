import { useState } from 'react';
import { CopyOutlined } from '@ant-design/icons';
import { App, Button, DatePicker, Form, Input, InputNumber, Select, Switch, Tabs } from 'antd';
import { cloneTariff, fetchOptions, fetchTariffs, optionsApi, tariffsApi } from '../../api/catalog';
import { deletePromoCode, fetchPromoCodes, savePromoCode } from '../../api/memberships';
import PageHeader from '../../components/PageHeader';
import CrudTable from '../../components/staff/CrudTable';
import { dayjs, ISO_DATE } from '../../utils/dates';
import { getErrorMessage } from '../../utils/errors';
import { days, formatMoney, sortTariffs, TARIFF_TYPE_LABELS } from '../../utils/format';

const loadTariffs = async () => sortTariffs(await fetchTariffs());

// Activate / deactivate right in the table (an inactive tariff or option is not sold)
function ActiveSwitch({ record, save, reload }) {
  const { message } = App.useApp();
  const [busy, setBusy] = useState(false);
  const toggle = async (checked) => {
    setBusy(true);
    try {
      await save(record.id, { is_active: checked });
      reload();
    } catch (err) {
      message.error(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };
  return <Switch size="small" checked={record.is_active} loading={busy} onChange={toggle} />;
}

const activeColumn = (save, reload) => ({
  title: 'Активний',
  dataIndex: 'is_active',
  width: 100,
  render: (_, record) => <ActiveSwitch record={record} save={save} reload={reload} />,
});

const priceRules = [{ required: true, message: 'Вкажіть ціну' }];

function TariffsTab() {
  const { message } = App.useApp();

  const columns = ({ reload }) => [
    { title: 'Назва', dataIndex: 'name' },
    { title: 'Тип', dataIndex: 'type', render: (t) => TARIFF_TYPE_LABELS[t] },
    { title: 'Ціна', dataIndex: 'price', render: formatMoney },
    { title: 'Тривалість', dataIndex: 'duration_days', render: days, responsive: ['lg'] },
    {
      title: 'Відвідувань',
      dataIndex: 'visit_limit',
      render: (v) => v ?? 'безліміт',
      responsive: ['md'],
    },
    activeColumn(tariffsApi.save, reload),
  ];

  // Prototype on the server: an inactive copy opens for editing right away
  const cloneAndEdit = async (tariff, { reload, edit }) => {
    try {
      const copy = await cloneTariff(tariff.id);
      message.success('Створено неактивну копію — відредагуйте й увімкніть її');
      reload();
      edit(copy);
    } catch (err) {
      message.error(getErrorMessage(err));
    }
  };

  return (
    <CrudTable
      load={loadTariffs}
      save={tariffsApi.save}
      remove={tariffsApi.remove}
      columns={columns}
      addLabel="Створити тариф"
      entityName="тариф"
      modalWidth={600}
      defaults={{ type: 'monthly', is_active: true }}
      toPayload={(v) => ({
        ...v,
        visit_limit: v.visit_limit ?? null,
        description: v.description || null,
      })}
      rowActions={(tariff, ctx) => (
        <Button size="small" icon={<CopyOutlined />} onClick={() => cloneAndEdit(tariff, ctx)}>
          На основі
        </Button>
      )}
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
            name="type"
            label="Тип (визначає, як рахується строк дії)"
            rules={[{ required: true }]}
          >
            <Select
              options={Object.entries(TARIFF_TYPE_LABELS).map(([value, label]) => ({
                value,
                label,
              }))}
            />
          </Form.Item>
          <Form.Item name="price" label="Ціна, грн" rules={priceRules}>
            <InputNumber min={0} step={50} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="duration_days"
            label="Тривалість, днів"
            rules={[{ required: true, message: 'Вкажіть тривалість' }]}
            extra="Місячний, піврічний і річний рахуються календарними місяцями"
          >
            <InputNumber min={1} max={1098} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="visit_limit"
            label="Ліміт відвідувань"
            extra="Порожньо — безліміт; для разового — 1"
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="description" label="Опис для клієнтів">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="is_active" label="Продається" valuePropName="checked">
            <Switch />
          </Form.Item>
        </>
      )}
    />
  );
}

function OptionsTab() {
  return (
    <CrudTable
      load={fetchOptions}
      save={optionsApi.save}
      remove={optionsApi.remove}
      columns={({ reload }) => [
        { title: 'Опція', dataIndex: 'name' },
        { title: 'Ціна', dataIndex: 'price', render: formatMoney },
        activeColumn(optionsApi.save, reload),
      ]}
      addLabel="Додати опцію"
      entityName="опцію"
      defaults={{ is_active: true }}
      renderForm={() => (
        <>
          <Form.Item
            name="name"
            label="Назва"
            rules={[{ required: true, min: 2, max: 100, message: 'Від 2 до 100 символів' }]}
          >
            <Input placeholder="Сауна" />
          </Form.Item>
          <Form.Item name="price" label="Ціна, грн" rules={priceRules}>
            <InputNumber min={0} step={50} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="is_active" label="Продається" valuePropName="checked">
            <Switch />
          </Form.Item>
        </>
      )}
    />
  );
}

function PromoCodesTab() {
  return (
    <CrudTable
      load={fetchPromoCodes}
      save={savePromoCode}
      remove={deletePromoCode}
      columns={[
        { title: 'Код', dataIndex: 'code' },
        { title: 'Знижка', dataIndex: 'percent', render: (p) => `${p}%` },
        {
          title: 'Діє до',
          dataIndex: 'valid_until',
          render: (d) => (d ? dayjs(d).format('DD.MM.YYYY') : 'без строку'),
        },
        { title: 'Активний', dataIndex: 'is_active', render: (a) => (a ? 'так' : 'ні') },
      ]}
      addLabel="Створити промокод"
      entityName="промокод"
      defaults={{ is_active: true, percent: 10 }}
      toForm={(p) => ({ ...p, valid_until: p.valid_until ? dayjs(p.valid_until) : null })}
      toPayload={(v) => ({
        ...v,
        valid_until: v.valid_until ? v.valid_until.format(ISO_DATE) : null,
      })}
      renderForm={() => (
        <>
          <Form.Item
            name="code"
            label="Код"
            normalize={(v) => v.toUpperCase()}
            rules={[
              { required: true, message: 'Вкажіть код' },
              { pattern: /^[A-Za-z0-9_-]{3,30}$/, message: '3–30 латинських літер, цифр, _ або -' },
            ]}
          >
            <Input placeholder="AUTUMN10" />
          </Form.Item>
          <Form.Item name="percent" label="Знижка, %" rules={[{ required: true }]}>
            <InputNumber min={1} max={90} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="valid_until" label="Діє до (включно)">
            <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="is_active" label="Активний" valuePropName="checked">
            <Switch />
          </Form.Item>
        </>
      )}
    />
  );
}

// Ф-5: tariff plans, extra options and promo codes (the discount strategies need them)
export default function TariffsPage() {
  return (
    <>
      <PageHeader title="Тарифи та знижки" subtitle="Що продається клієнтам і за якою ціною" />
      <Tabs
        items={[
          { key: 'tariffs', label: 'Тарифи', children: <TariffsTab /> },
          { key: 'options', label: 'Додаткові опції', children: <OptionsTab /> },
          { key: 'promo', label: 'Промокоди', children: <PromoCodesTab /> },
        ]}
      />
    </>
  );
}
