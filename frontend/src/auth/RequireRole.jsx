import { Navigate, Outlet, useLocation } from 'react-router-dom';
import PageSpinner from '../components/PageSpinner';
import useAuth from './useAuth';

// Route guard: only hides pages from the UI. The real access check is on the server (403).
export default function RequireRole({ roles }) {
  const { user, status } = useAuth();
  const location = useLocation();

  if (status === 'loading') return <PageSpinner />;
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }
  if (!roles.includes(user.role)) return <Navigate to="/403" replace />;
  return <Outlet />;
}
