import { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchMe, login, register } from '../api/auth';
import { getStoredToken, onUnauthorized, storeToken } from '../api/client';
import AuthContext from './AuthContext';

// Keeps the signed-in user: the JWT lives in localStorage, the user is re-read from /auth/me
export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState(() => (getStoredToken() ? 'loading' : 'ready'));

  const logout = useCallback(() => {
    storeToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    onUnauthorized(logout);
    if (!getStoredToken()) return;
    fetchMe()
      .then(setUser)
      .catch(() => storeToken(null))
      .finally(() => setStatus('ready'));
  }, [logout]);

  const applyToken = useCallback((data) => {
    storeToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const signIn = useCallback(
    async (email, password) => applyToken(await login(email, password)),
    [applyToken],
  );

  const signUp = useCallback(async (payload) => applyToken(await register(payload)), [applyToken]);

  const value = useMemo(
    () => ({ user, status, signIn, signUp, logout }),
    [user, status, signIn, signUp, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
