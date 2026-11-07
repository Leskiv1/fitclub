import { Tag } from 'antd';
import { BOOKING_STATUS, MEMBERSHIP_STATUS } from '../utils/format';

// Colors of the membership states (State pattern on the server) and of booking statuses
export function MembershipStatusTag({ status }) {
  const { label, color } = MEMBERSHIP_STATUS[status] ?? { label: status, color: 'default' };
  return <Tag color={color}>{label}</Tag>;
}

export function BookingStatusTag({ status }) {
  const { label, color } = BOOKING_STATUS[status] ?? { label: status, color: 'default' };
  return <Tag color={color}>{label}</Tag>;
}
