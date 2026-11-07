import apiClient from './client';

// week: any date of the week (YYYY-MM-DD); the server returns Monday..Sunday
export async function fetchWeekSessions({ week, kind, trainerId } = {}) {
  const { data } = await apiClient.get('/sessions', {
    params: { week, kind, trainer_id: trainerId },
  });
  return data;
}

// Free one-hour slots of a trainer on a day, as ISO datetimes in the club time zone
export async function fetchTrainerSlots(trainerId, date) {
  const { data } = await apiClient.get(`/trainers/${trainerId}/slots`, { params: { date } });
  return data;
}

// Staff or the trainer of the session
export async function fetchParticipants(sessionId) {
  const { data } = await apiClient.get(`/sessions/${sessionId}/participants`);
  return data;
}

// --- Admin: group sessions (Ф-4) ---

export async function saveSession(id, payload) {
  const { data } = id
    ? await apiClient.patch(`/sessions/${id}`, payload)
    : await apiClient.post('/sessions', payload);
  return data;
}

export async function deleteSession(id) {
  await apiClient.delete(`/sessions/${id}`);
}

// Prototype on the server: clones every group session of a week; conflicts are skipped with a reason
export async function copyWeek(sourceMonday, targetMonday) {
  const { data } = await apiClient.post('/sessions/copy-week', {
    source_week: sourceMonday,
    target_week: targetMonday,
  });
  return data;
}
