import axios from 'axios';

// All requests go to /api; in development Vite proxies them to the FastAPI server
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

const TOKEN_KEY = 'fitclub.token';
let unauthorizedHandler = null;

export function getStoredToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function storeToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Storage is unavailable (private mode): the session lives until the tab is closed
  }
}

// AuthProvider registers a callback that signs the user out when the token expires
export function onUnauthorized(handler) {
  unauthorizedHandler = handler;
}

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // 401 with a token means the token expired; 401 on login (wrong password) has no token
    const hadToken = Boolean(error.config?.headers?.Authorization);
    if (error.response?.status === 401 && hadToken && unauthorizedHandler) {
      unauthorizedHandler();
    }
    return Promise.reject(error);
  },
);

export default apiClient;
