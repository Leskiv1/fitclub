import apiClient from './client';

// payload: { tariff_id, option_ids, discount: { type, reference } | null }

// Price breakdown without saving anything (Facade -> Decorator -> Strategy on the server)
export async function quoteMembership(payload) {
  const { data } = await apiClient.post('/memberships/quote', payload);
  return data;
}

// Clients always pay online (payment is simulated)
export async function purchaseMembership(payload) {
  const { data } = await apiClient.post('/memberships', { ...payload, payment_method: 'online' });
  return data;
}

export async function fetchClientMemberships(clientId) {
  const { data } = await apiClient.get(`/clients/${clientId}/memberships`);
  return data;
}
