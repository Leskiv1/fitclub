import { useState } from 'react';
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import { Alert, App, Button, Flex, Form, Modal, Popconfirm, Table } from 'antd';
import useApi from '../../hooks/useApi';
import { getErrorMessage } from '../../utils/errors';
import LoadError from '../LoadError';

// Admin list of one entity (ЗВ-7): table + create/edit modal + delete.
// What differs between halls, options, promo codes, tariffs and trainers is passed in as config.
export default function CrudTable({
  load, // memoized () => Promise<list>
  save, // (id | null, payload) => Promise
  remove, // (id) => Promise
  columns, // array, or ({ reload, edit }) => array when cells need to refresh the list
  renderForm, // (record | null) => <Form.Item>s
  toForm = (record) => record, // record -> initial form values
  toPayload = (values) => values, // form values -> request body
  addLabel,
  entityName, // genitive, e.g. "зал"
  modalWidth = 520,
  rowActions, // (record, { reload, edit }) => extra buttons
  defaults = {}, // initial values for a new record
}) {
  const { message } = App.useApp();
  const { data, error, loading, reload } = useApi(load);
  const [editing, setEditing] = useState(null); // { record } — record is null for a new one
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [form] = Form.useForm();

  const open = (record) => {
    setSaveError(null);
    setEditing({ record });
  };

  const submit = async () => {
    let values;
    try {
      values = await form.validateFields();
    } catch {
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      await save(editing.record?.id ?? null, toPayload(values, editing.record));
      message.success('Збережено');
      setEditing(null);
      reload();
    } catch (err) {
      setSaveError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const del = async (record) => {
    try {
      await remove(record.id);
      message.success('Видалено');
      reload();
    } catch (err) {
      message.error(getErrorMessage(err));
    }
  };

  const actionsColumn = {
    title: '',
    key: 'actions',
    align: 'right',
    render: (_, record) => (
      <Flex gap={4} justify="end" wrap>
        {rowActions?.(record, { reload, edit: open })}
        <Button size="small" icon={<EditOutlined />} onClick={() => open(record)}>
          Змінити
        </Button>
        <Popconfirm
          title={`Видалити ${entityName}?`}
          okText="Видалити"
          okButtonProps={{ danger: true }}
          cancelText="Ні"
          onConfirm={() => del(record)}
        >
          <Button size="small" danger icon={<DeleteOutlined />} aria-label="Видалити" />
        </Popconfirm>
      </Flex>
    ),
  };

  if (error && !data) return <LoadError error={error} onRetry={reload} />;

  return (
    <>
      <Flex justify="end" style={{ marginBottom: 12 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => open(null)}>
          {addLabel}
        </Button>
      </Flex>
      <Table
        rowKey="id"
        columns={[
          ...(typeof columns === 'function' ? columns({ reload, edit: open }) : columns),
          actionsColumn,
        ]}
        dataSource={data ?? []}
        loading={loading}
        pagination={{ pageSize: 20, hideOnSinglePage: true }}
        scroll={{ x: 'max-content' }}
      />
      <Modal
        open={Boolean(editing)}
        title={editing?.record ? `Змінити ${entityName}` : addLabel}
        width={modalWidth}
        onCancel={() => setEditing(null)}
        onOk={submit}
        okText="Зберегти"
        cancelText="Скасувати"
        confirmLoading={saving}
        destroyOnHidden
      >
        {saveError && (
          <Alert type="error" showIcon title={saveError} style={{ marginBottom: 16 }} />
        )}
        {editing && (
          <Form
            key={editing.record?.id ?? 'new'}
            form={form}
            layout="vertical"
            requiredMark={false}
            initialValues={editing.record ? toForm(editing.record) : defaults}
          >
            {renderForm(editing.record)}
          </Form>
        )}
      </Modal>
    </>
  );
}
