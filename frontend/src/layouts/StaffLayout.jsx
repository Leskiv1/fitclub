import { Suspense } from 'react';
import { LogoutOutlined } from '@ant-design/icons';
import { Avatar, Button, Flex, Grid, Layout, Menu, Typography } from 'antd';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { ROLE_LABELS } from '../auth/roles';
import { menuFor } from '../auth/staffMenu';
import useAuth from '../auth/useAuth';
import Logo from '../components/Logo';
import PageSpinner from '../components/PageSpinner';
import { initials } from '../utils/format';

const { Sider, Header, Content } = Layout;
const { Text } = Typography;

// Staff workspace: graphite side menu (as in the Stitch mockups) with sections of the user's role
export default function StaffLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const screens = Grid.useBreakpoint();
  const items = menuFor(user.role);
  const selected = items.find((item) => location.pathname.startsWith(item.path))?.path;

  const signOut = () => {
    logout();
    navigate('/');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={240} breakpoint="lg" collapsedWidth={0} className="staff-sider">
        <Flex vertical style={{ height: '100%' }}>
          <div className="staff-sider__brand">
            <Logo to="/staff" light />
            <Text className="staff-sider__caption">Кабінет персоналу</Text>
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={selected ? [selected] : []}
            items={items.map(({ path, label, icon: Icon }) => ({
              key: path,
              icon: <Icon />,
              label: <Link to={path}>{label}</Link>,
            }))}
            style={{ flex: 1, borderInlineEnd: 'none' }}
          />
          <Flex align="center" gap={12} className="staff-sider__user">
            <Avatar style={{ background: 'var(--fc-primary)', flexShrink: 0 }}>
              {initials(user.full_name ?? user.email)}
            </Avatar>
            <Flex vertical style={{ minWidth: 0, flex: 1 }}>
              <Text ellipsis style={{ color: '#fff' }}>
                {user.full_name ?? user.email}
              </Text>
              <Text style={{ color: '#c3c6ce', fontSize: 12 }}>{ROLE_LABELS[user.role]}</Text>
            </Flex>
            <Button
              type="text"
              icon={<LogoutOutlined />}
              onClick={signOut}
              aria-label="Вийти"
              style={{ color: '#c3c6ce' }}
            />
          </Flex>
        </Flex>
      </Sider>
      <Layout>
        {!screens.lg && <Header className="app-header" style={{ paddingLeft: 64 }} />}
        <Content className="page page--wide">
          <Suspense fallback={<PageSpinner />}>
            <Outlet />
          </Suspense>
        </Content>
      </Layout>
    </Layout>
  );
}
