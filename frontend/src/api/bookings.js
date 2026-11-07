import apiClient from './client';

// A client books only for themselves: the server takes client_id from the token

export async function bookGroupSession(sessionId) {
  const { data } = await apiClient.post('/bookings', { session_id: sessionId });
  return data;
}

export async function bookIndividual(trainerId, startAt) {
  const { data } = await apiClient.post('/bookings/individual', {
    trainer_id: trainerId,
    start_at: startAt,
  });
  return data;
}

export async function cancelBooking(bookingId) {
  const { data } = await apiClient.post(`/bookings/${bookingId}/cancel`);
  return data;
}

// Command pattern on the server: undoes the user's last book/cancel action
export async function undoLastBookingAction() {
  const { data } = await apiClient.post('/bookings/undo');
  return data;
}

export async function fetchClientBookings(clientId, upcoming) {
  const { data } = await apiClient.get(`/clients/${clientId}/bookings`, {
    params: { upcoming },
  });
  return data;
}
