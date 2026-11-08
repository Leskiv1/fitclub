import apiClient from './client';

// payload: { tariff_id, option_ids, discount: { type, reference } | null, client_id? }
// client_id is taken from the token for a client and is required for staff

// Price breakdown without saving anything (Facade -> Decorator -> Strategy on the server)
export async function quoteMembership(payload) {
  const { data } = await apiClient.post('/memberships/quote', payload);
  return data;
}

// Clients always pay online (simulated); staff take cash or card at the reception
export async function purchaseMembership(payload, paymentMethod = 'online') {
  const { data } = await apiClient.post('/memberships', {
    ...payload,
    payment_method: paymentMethod,
  });
  return data;
}

export async function fetchClientMemberships(clientId) {
  const { data } = await apiClient.get(`/clients/${clientId}/memberships`);
  return data;
}

// State transitions (State pattern on the server): active <-> frozen, any open one -> cancelled
export async function changeMembershipState(membershipId, action) {
  const { data } = await apiClient.post(`/memberships/${membershipId}/${action}`);
  return data;
}

export async function fetchPromoCodes() {
  const { data } = await apiClient.get('/promo-codes', { params: { limit: 100 } });
  return data.items;
}

export async function savePromoCode(id, payload) {
  const { data } = id
    ? await apiClient.patch(`/promo-codes/${id}`, payload)
    : await apiClient.post('/promo-codes', payload);
  return data;
}

export async function deletePromoCode(id) {
  await apiClient.delete(`/promo-codes/${id}`);
}
