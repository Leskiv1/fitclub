import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import RequireRole from './auth/RequireRole';
import { CLIENT, STAFF_ROLES } from './auth/roles';
import { rolesFor } from './auth/staffMenu';
import PageSpinner from './components/PageSpinner';
import PublicLayout from './layouts/PublicLayout';

// Code splitting: every page is a separate chunk, loaded on first visit (Suspense is in the layouts).
// The client and staff layouts are lazy too: guests on the landing page never need them.
const ClientLayout = lazy(() => import('./layouts/ClientLayout'));
const StaffLayout = lazy(() => import('./layouts/StaffLayout'));
const HomePage = lazy(() => import('./pages/HomePage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const ForbiddenPage = lazy(() => import('./pages/ForbiddenPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));
const MyMembershipPage = lazy(() => import('./pages/client/MyMembershipPage'));
const SchedulePage = lazy(() => import('./pages/client/SchedulePage'));
const IndividualBookingPage = lazy(() => import('./pages/client/IndividualBookingPage'));
const MyBookingsPage = lazy(() => import('./pages/client/MyBookingsPage'));
const PurchasePage = lazy(() => import('./pages/client/PurchasePage'));
const StaffIndexPage = lazy(() => import('./pages/staff/StaffIndexPage'));
const CheckInPage = lazy(() => import('./pages/staff/CheckInPage'));
const ClientsPage = lazy(() => import('./pages/staff/ClientsPage'));
const ClientDetailPage = lazy(() => import('./pages/staff/ClientDetailPage'));
const TrainerCabinetPage = lazy(() => import('./pages/staff/TrainerCabinetPage'));
const DashboardPage = lazy(() => import('./pages/staff/DashboardPage'));
const AdminSchedulePage = lazy(() => import('./pages/staff/SchedulePage'));
const TrainersPage = lazy(() => import('./pages/staff/TrainersPage'));
const TrainerProfilePage = lazy(() => import('./pages/staff/TrainerProfilePage'));
const HallsPage = lazy(() => import('./pages/staff/HallsPage'));
const TariffsPage = lazy(() => import('./pages/staff/TariffsPage'));
const ReportsPage = lazy(() => import('./pages/staff/ReportsPage'));
const SettingsPage = lazy(() => import('./pages/staff/SettingsPage'));

const lazyLayout = (Layout) => (
  <Suspense fallback={<PageSpinner />}>
    <Layout />
  </Suspense>
);

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/403" element={<ForbiddenPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      <Route element={<RequireRole roles={[CLIENT]} />}>
        <Route path="/my" element={lazyLayout(ClientLayout)}>
          <Route index element={<MyMembershipPage />} />
          <Route path="schedule" element={<SchedulePage />} />
          <Route path="individual" element={<IndividualBookingPage />} />
          <Route path="bookings" element={<MyBookingsPage />} />
          <Route path="purchase" element={<PurchasePage />} />
        </Route>
      </Route>

      {/* Role groups come from auth/staffMenu.js, the same list that builds the side menu */}
      <Route element={<RequireRole roles={STAFF_ROLES} />}>
        <Route path="/staff" element={lazyLayout(StaffLayout)}>
          <Route index element={<StaffIndexPage />} />
          <Route element={<RequireRole roles={rolesFor('/staff/check-in')} />}>
            <Route path="check-in" element={<CheckInPage />} />
            <Route path="clients" element={<ClientsPage />} />
            <Route path="clients/:clientId" element={<ClientDetailPage />} />
          </Route>
          <Route element={<RequireRole roles={rolesFor('/staff/trainer')} />}>
            <Route path="trainer" element={<TrainerCabinetPage />} />
          </Route>
          <Route element={<RequireRole roles={rolesFor('/staff/dashboard')} />}>
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="schedule" element={<AdminSchedulePage />} />
            <Route path="trainers" element={<TrainersPage />} />
            <Route path="trainers/:trainerId" element={<TrainerProfilePage />} />
            <Route path="halls" element={<HallsPage />} />
            <Route path="tariffs" element={<TariffsPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}
