import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import RequireRole from './auth/RequireRole';
import { CLIENT, STAFF_ROLES } from './auth/roles';
import PageSpinner from './components/PageSpinner';
import PublicLayout from './layouts/PublicLayout';

// Code splitting: every page is a separate chunk, loaded on first visit (Suspense is in the layouts).
// The client layout (menu, notifications) is lazy too: guests on the landing page never need it.
const ClientLayout = lazy(() => import('./layouts/ClientLayout'));
const HomePage = lazy(() => import('./pages/HomePage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const ForbiddenPage = lazy(() => import('./pages/ForbiddenPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));
const StaffHomePage = lazy(() => import('./pages/StaffHomePage'));
const MyMembershipPage = lazy(() => import('./pages/client/MyMembershipPage'));
const SchedulePage = lazy(() => import('./pages/client/SchedulePage'));
const IndividualBookingPage = lazy(() => import('./pages/client/IndividualBookingPage'));
const MyBookingsPage = lazy(() => import('./pages/client/MyBookingsPage'));
const PurchasePage = lazy(() => import('./pages/client/PurchasePage'));

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/403" element={<ForbiddenPage />} />
        <Route element={<RequireRole roles={STAFF_ROLES} />}>
          <Route path="/staff" element={<StaffHomePage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      <Route element={<RequireRole roles={[CLIENT]} />}>
        <Route
          path="/my"
          element={
            <Suspense fallback={<PageSpinner />}>
              <ClientLayout />
            </Suspense>
          }
        >
          <Route index element={<MyMembershipPage />} />
          <Route path="schedule" element={<SchedulePage />} />
          <Route path="individual" element={<IndividualBookingPage />} />
          <Route path="bookings" element={<MyBookingsPage />} />
          <Route path="purchase" element={<PurchasePage />} />
        </Route>
      </Route>
    </Routes>
  );
}
