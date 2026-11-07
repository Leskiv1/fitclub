import { Flex, Form, Input, Typography } from 'antd';
import { Link } from 'react-router-dom';
import { fetchTrainers, trainersApi } from '../../api/catalog';
import PageHeader from '../../components/PageHeader';
import TrainerAvatar from '../../components/TrainerAvatar';
import CrudTable from '../../components/staff/CrudTable';
import WeekHoursInput from '../../components/staff/WeekHoursInput';
import { WEEKDAYS_SHORT } from '../../utils/format';
import { emailRules, nameRules, passwordRules } from '../../utils/validation';
import { shiftsToWeek, weekToShifts } from '../../utils/workShifts';

const { Text } = Typography;

const columns = [
  {
    title: 'Тренер',
    dataIndex: 'full_name',
    render: (name, t) => (
      <Flex gap={12} align="center">
        <TrainerAvatar trainer={t} size={36} />
        <Link to={`/staff/trainers/${t.id}`}>{name}</Link>
      </Flex>
    ),
  },
  { title: 'Спеціалізація', dataIndex: 'specialization', responsive: ['md'] },
  {
    title: 'Робочі дні',
    dataIndex: 'work_shifts',
    responsive: ['lg'],
    render: (shifts) =>
      shifts.length ? (
        [...shifts]
          .sort((a, b) => a.weekday - b.weekday)
          .map((s) => WEEKDAYS_SHORT[s.weekday])
          .join(', ')
      ) : (
        <Text type="secondary">не задано</Text>
      ),
  },
];

// Ф-3, ЗВ-7: trainers with their weekly shifts (shifts define free slots for individual sessions)
export default function TrainersPage() {
  return (
    <>
      <PageHeader
        title="Тренери"
        subtitle="Профіль, графік роботи і клієнти — за посиланням на імені тренера"
      />
      <CrudTable
        load={fetchTrainers}
        save={trainersApi.save}
        remove={trainersApi.remove}
        columns={columns}
        addLabel="Додати тренера"
        entityName="тренера"
        modalWidth={640}
        defaults={{ work_shifts: {} }}
        toForm={(t) => ({ ...t, work_shifts: shiftsToWeek(t.work_shifts) })}
        toPayload={(values) => ({
          ...values,
          photo_url: values.photo_url || null,
          work_shifts: weekToShifts(values.work_shifts ?? {}),
        })}
        renderForm={(trainer) => (
          <>
            <Form.Item name="full_name" label="Імʼя та прізвище" rules={nameRules}>
              <Input />
            </Form.Item>
            <Form.Item
              name="specialization"
              label="Спеціалізація"
              rules={[{ required: true, min: 2, max: 150, message: 'Від 2 до 150 символів' }]}
            >
              <Input placeholder="Йога, пілатес, стретчинг" />
            </Form.Item>
            <Form.Item name="bio" label="Про тренера">
              <Input.TextArea rows={2} />
            </Form.Item>
            <Form.Item name="photo_url" label="Посилання на фото" rules={[{ type: 'url' }]}>
              <Input placeholder="https://…" />
            </Form.Item>
            <Form.Item name="email" label="Email для входу" rules={emailRules}>
              <Input />
            </Form.Item>
            {!trainer && (
              <Form.Item name="password" label="Пароль" rules={passwordRules}>
                <Input.Password autoComplete="new-password" />
              </Form.Item>
            )}
            <Form.Item name="work_shifts" label="Графік роботи">
              <WeekHoursInput />
            </Form.Item>
          </>
        )}
      />
    </>
  );
}
