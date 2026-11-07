import apiClient from './client';

// Ф-2: the server runs the Chain of Responsibility; a refusal is 422 with the reason code
export async function checkIn(clientId) {
  const { data } = await apiClient.post('/check-ins', { client_id: clientId });
  return data;
}

export async function fetchTodayVisits() {
  const { data } = await apiClient.get('/check-ins/today');
  return data;
}

// [{ date, visits }] for the last `days` days, zeros included
export async function fetchDailyVisits(days = 14) {
  const { data } = await apiClient.get('/check-ins/daily', { params: { days } });
  return data;
}
