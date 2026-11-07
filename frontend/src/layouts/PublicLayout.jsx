import { Suspense } from 'react';
import { Button, Flex, Layout } from 'antd';
import { Link, Outlet } from 'react-router-dom';
import { homePathFor } from '../auth/roles';
import useAuth from '../auth/useAuth';
import Logo from '../components/Logo';
import PageSpinner from '../components/PageSpinner';

const { Header, Content, Footer } = Layout;

// Landing, sign in and sign up: open to guests
export default function PublicLayout() {
  const { user } = useAuth();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header className="app-header">
        <Logo />
        <Flex gap={8}>
          {user ? (
            <Link to={homePathFor(user)}>
              <Button type="primary">Мій кабінет</Button>
            </Link>
          ) : (
            <>
              <Link to="/login">
                <Button>Увійти</Button>
              </Link>
              <Link to="/register" className="hide-xs">
                <Button type="primary">Реєстрація</Button>
              </Link>
            </>
          )}
        </Flex>
      </Header>
      <Content>
        <Suspense fallback={<PageSpinner />}>
          <Outlet />
        </Suspense>
      </Content>
      <Footer className="app-footer">© {new Date().getFullYear()} FitClub</Footer>
    </Layout>
  );
}
