import { Button, Result } from 'antd';
import { useNavigate } from 'react-router-dom';
import useAuth from '../auth/useAuth';

const ROLE_LABELS = { trainer: 'Тренер', reception: 'Рецепція', admin: 'Адміністратор' };

// Landing page for staff after sign in; the reception, trainer and admin sections replace it in stage 11
export default function StaffHomePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <Result
      status="info"
      title={`Вітаємо, ${user.full_name ?? user.email}!`}
      subTitle={`Роль: ${ROLE_LABELS[user.role]}. Робочі розділи для персоналу ще в розробці.`}
      extra={
        <Button
          onClick={() => {
            logout();
            navigate('/');
          }}
        >
          Вийти
        </Button>
      }
    />
  );
}
