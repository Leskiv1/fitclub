import { Suspense } from 'react';
import {
  CalendarOutlined,
  CreditCardOutlined,
  IdcardOutlined,
  LogoutOutlined,
  ScheduleOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Avatar, Button, Dropdown, Flex, Grid, Layout, Menu } from 'antd';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import useAuth from '../auth/useAuth';
import Logo from '../components/Logo';
import NotificationBell from '../components/NotificationBell';
import PageSpinner from '../components/PageSpinner';
import { initials } from '../utils/format';

const { Header, Content } = Layout;

const NAV = [
  { path: '/my', label: 'Абонемент', icon: <IdcardOutlined /> },
  { path: '/my/schedule', label: 'Розклад', icon: <CalendarOutlined /> },
  { path: '/my/individual', label: 'Персональні', icon: <UserOutlined /> },
  { path: '/my/bookings', label: 'Мої записи', icon: <ScheduleOutlined /> },
  { path: '/my/purchase', label: 'Купити', icon: <CreditCardOutlined /> },
];

// Client cabinet: top menu on desktop, bottom tab bar on phones (as in the Stitch mockups)
export default function ClientLayout() {
  const { user, logout } = useAuth();
  const screens = Grid.useBreakpoint();
  const location = useLocation();
  const navigate = useNavigate();
  const isDesktop = screens.md;

  const userMenu = {
    items: [
      { key: 'name', label: user.full_name ?? user.email, disabled: true },
      { type: 'divider' },
      { key: 'logout', label: 'Вийти', icon: <LogoutOutlined />, danger: true },
    ],
    onClick: ({ key }) => {
      if (key === 'logout') {
        logout();
        navigate('/');
      }
    },
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header className="app-header">
        <Logo to="/my" />
        {isDesktop && (
          <Menu
            mode="horizontal"
            selectedKeys={[location.pathname]}
            items={NAV.map((item) => ({
              key: item.path,
              icon: item.icon,
              label: <NavLink to={item.path}>{item.label}</NavLink>,
            }))}
            style={{ flex: 1, minWidth: 0, justifyContent: 'center', borderBottom: 'none' }}
          />
        )}
        <Flex gap={8} align="center">
          <NotificationBell clientId={user.client_id} />
          <Dropdown menu={userMenu} trigger={['click']} placement="bottomRight">
            <Button type="text" shape="circle" aria-label="Профіль">
              <Avatar size={32} style={{ background: 'var(--fc-graphite)' }}>
                {initials(user.full_name ?? user.email)}
              </Avatar>
            </Button>
          </Dropdown>
        </Flex>
      </Header>

      <Content className={`page ${isDesktop ? '' : 'page--with-tabbar'}`}>
        <Suspense fallback={<PageSpinner />}>
          <Outlet />
        </Suspense>
      </Content>

      {!isDesktop && (
        <nav className="tabbar">
          {NAV.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end
              className={({ isActive }) => `tabbar__item ${isActive ? 'tabbar__item--active' : ''}`}
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      )}
    </Layout>
  );
}
