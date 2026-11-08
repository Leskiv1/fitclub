import apiClient from './client';

// Client card with the current membership chosen by the server
export async function fetchClient(clientId) {
  const { data } = await apiClient.get(`/clients/${clientId}`);
  return data;
}

export async function fetchClientVisits(clientId, limit = 100, offset = 0) {
  const { data } = await apiClient.get(`/clients/${clientId}/visits`, {
    params: { limit, offset },
  });
  return data;
}

export async function fetchClientNotifications(clientId, limit = 10) {
  const { data } = await apiClient.get(`/clients/${clientId}/notifications`, {
    params: { limit },
  });
  return data;
}

// Staff: client registry (Ф-1) with search by name or phone
export async function searchClients({ q, offset = 0, limit = 20 } = {}) {
  const { data } = await apiClient.get('/clients', {
    params: { q: q || undefined, offset, limit },
  });
  return data;
}

export async function createClient(payload) {
  const { data } = await apiClient.post('/clients', payload);
  return data;
}

export async function updateClient(clientId, payload) {
  const { data } = await apiClient.patch(`/clients/${clientId}`, payload);
  return data;
}

export async function deleteClient(clientId) {
  await apiClient.delete(`/clients/${clientId}`);
}
