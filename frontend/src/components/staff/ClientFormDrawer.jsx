import { useState } from 'react';
import { Alert, Button, DatePicker, Drawer, Flex, Form, Input, Radio } from 'antd';
import { createClient, updateClient } from '../../api/clients';
import { dayjs, ISO_DATE } from '../../utils/dates';
import { getErrorMessage } from '../../utils/errors';
import { CHANNEL_LABELS } from '../../utils/format';
import {
  emailRules,
  nameRules,
  normalizePhone,
  passwordRules,
  phoneRules,
} from '../../utils/validation';

// New client (reception) or edit of an existing one. On create the client gets an account
// with the given password; "Зберегти та оформити абонемент" continues to the sale.
export default function ClientFormDrawer({ client, open, onClose, onSaved }) {
  const [form] = Form.useForm();
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const isNew = !client;

  const save = async (sell) => {
    let values;
    try {
      values = await form.validateFields();
    } catch {
      return; // the form shows the field errors
    }
    setSaving(true);
    setError(null);
    const payload = {
      ...values,
      full_name: values.full_name.trim(),
      birth_date: values.birth_date.format(ISO_DATE),
    };
    try {
      const saved = isNew ? await createClient(payload) : await updateClient(client.id, payload);
      onSaved(saved, { sell });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={isNew ? 'Новий клієнт' : 'Редагувати клієнта'}
      size={480}
      destroyOnHidden
      footer={
        <Flex gap={8} wrap justify="end">
          <Button onClick={onClose}>Скасувати</Button>
          {isNew && (
            <Button loading={saving} onClick={() => save(true)}>
              Зберегти та оформити абонемент
            </Button>
          )}
          <Button type="primary" loading={saving} onClick={() => save(false)}>
            Зберегти
          </Button>
        </Flex>
      }
    >
      {error && <Alert type="error" showIcon title={error} style={{ marginBottom: 16 }} />}
      <Form
        form={form}
        layout="vertical"
        requiredMark={false}
        initialValues={
          client
            ? { ...client, birth_date: dayjs(client.birth_date) }
            : { notification_channel: 'email' }
        }
      >
        <Form.Item name="full_name" label="Прізвище та імʼя" rules={nameRules}>
          <Input placeholder="Шевченко Тарас" />
        </Form.Item>
        <Form.Item
          name="birth_date"
          label="Дата народження"
          rules={[{ required: true, message: 'Оберіть дату народження' }]}
        >
          <DatePicker
            format="DD.MM.YYYY"
            style={{ width: '100%' }}
            disabledDate={(d) => d.isAfter(dayjs())}
            defaultPickerValue={dayjs().subtract(25, 'year')}
          />
        </Form.Item>
        <Form.Item name="phone" label="Телефон" normalize={normalizePhone} rules={phoneRules}>
          <Input placeholder="+380671234567" />
        </Form.Item>
        <Form.Item name="email" label="Email" rules={emailRules}>
          <Input />
        </Form.Item>
        {isNew && (
          <Form.Item
            name="password"
            label="Пароль для входу в кабінет"
            rules={passwordRules}
            extra="Передайте клієнту — він зможе змінити його пізніше"
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>
        )}
        <Form.Item name="notification_channel" label="Канал сповіщень">
          <Radio.Group
            optionType="button"
            options={Object.entries(CHANNEL_LABELS).map(([value, label]) => ({ value, label }))}
          />
        </Form.Item>
      </Form>
    </Drawer>
  );
}
