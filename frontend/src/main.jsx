import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { App as AntApp, ConfigProvider } from 'antd';
import ukUA from 'antd/locale/uk_UA';
import App from './App';
import AuthProvider from './auth/AuthProvider';
import theme from './theme/theme';
import './utils/dates';
import './index.css';

// AntApp gives message/notification/modal hooks that use this theme and locale
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ConfigProvider theme={theme} locale={ukUA}>
      <AntApp>
        <BrowserRouter>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  </StrictMode>,
);
