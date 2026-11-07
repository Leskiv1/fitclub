import { useParams } from 'react-router-dom';
import TrainerWorkspace from '../../components/staff/TrainerWorkspace';

// Admin view of any trainer: the same workspace the trainer sees
export default function TrainerProfilePage() {
  const { trainerId } = useParams();
  return <TrainerWorkspace trainerId={Number(trainerId)} />;
}
