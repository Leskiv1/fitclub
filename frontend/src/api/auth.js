import apiClient from './client';

export async function login(email, password) {
  const { data } = await apiClient.post('/auth/login', { email, password });
  return data;
}

export async function register(payload) {
  const { data } = await apiClient.post('/auth/register', payload);
  return data;
}

export async function fetchMe() {
  const { data } = await apiClient.get('/auth/me');
  return data;
}
