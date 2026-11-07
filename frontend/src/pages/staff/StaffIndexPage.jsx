import { Navigate } from 'react-router-dom';
import { staffHomeFor } from '../../auth/staffMenu';
import useAuth from '../../auth/useAuth';

// /staff itself: open the first section of the role's menu
export default function StaffIndexPage() {
  const { user } = useAuth();
  return <Navigate to={staffHomeFor(user.role)} replace />;
}
