import { Alert, Button } from 'antd';
import { Link } from 'react-router-dom';
import { getErrorCode, getErrorMessage } from '../utils/errors';

// Booking refusals (Chain of Responsibility on the server) that a new membership resolves
const NEEDS_MEMBERSHIP = ['no_membership', 'membership_expired', 'no_visits_left'];

export default function BookingErrorAlert({ error }) {
  if (!error) return null;
  return (
    <Alert
      type="error"
      showIcon
      title={getErrorMessage(error)}
      action={
        NEEDS_MEMBERSHIP.includes(getErrorCode(error)) && (
          <Link to="/my/purchase">
            <Button size="small" type="primary">
              Оформити абонемент
            </Button>
          </Link>
        )
      }
    />
  );
}
