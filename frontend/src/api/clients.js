import apiClient from './client';

// Client card with the current membership chosen by the server
export async function fetchClient(clientId) {
  const { data } = await apiClient.get(`/clients/${clientId}`);
  return data;
}

export async function fetchClientVisits(clientId, limit = 100) {
  const { data } = await apiClient.get(`/clients/${clientId}/visits`, { params: { limit } });
  return data;
}

export async function fetchClientNotifications(clientId, limit = 10) {
  const { data } = await apiClient.get(`/clients/${clientId}/notifications`, {
    params: { limit },
  });
  return data;
}
