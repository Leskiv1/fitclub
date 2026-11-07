import { Avatar } from 'antd';
import { initials } from '../utils/format';

// Photo if the trainer has one, otherwise initials on the brand color
export default function TrainerAvatar({ trainer, size = 48 }) {
  if (trainer.photo_url)
    return <Avatar src={trainer.photo_url} size={size} alt={trainer.full_name} />;
  return (
    <Avatar size={size} style={{ background: 'var(--fc-primary)', fontWeight: 700 }}>
      {initials(trainer.full_name)}
    </Avatar>
  );
}
