import { Result } from 'antd';
import useAuth from '../../auth/useAuth';
import TrainerWorkspace from '../../components/staff/TrainerWorkspace';

// The signed-in trainer's own workspace (trainer_id comes from /auth/me)
export default function TrainerCabinetPage() {
  const { user } = useAuth();
  if (!user.trainer_id) {
    return <Result status="warning" title="Обліковий запис не повʼязано з профілем тренера" />;
  }
  return <TrainerWorkspace trainerId={user.trainer_id} title="Мій кабінет" />;
}
