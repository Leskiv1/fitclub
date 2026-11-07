import apiClient from './client';

// Notification log (Ф-6) and the daily check run on demand
export async function fetchNotificationLog({ offset = 0, limit = 20, kind, status } = {}) {
  const { data } = await apiClient.get('/notifications', {
    params: { offset, limit, kind, status },
  });
  return data;
}

export async function runDailyCheck() {
  const { data } = await apiClient.post('/notifications/run-check');
  return data;
}

// Reports З-1..З-3: JSON for the screen (a tree of sections — Composite on the server)
export async function fetchReport(code, params) {
  const { data } = await apiClient.get(`/reports/${code}`, {
    params: { ...params, format: 'json' },
  });
  return data;
}

// CSV/PDF need the JWT header, so a plain link would not work: download as a blob and save it
export async function downloadReport(code, params, format) {
  const response = await apiClient.get(`/reports/${code}`, {
    params: { ...params, format },
    responseType: 'blob',
    timeout: 60000,
  });
  const disposition = response.headers['content-disposition'] ?? '';
  const filename = /filename="([^"]+)"/.exec(disposition)?.[1] ?? `${code}.${format}`;
  const url = URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
