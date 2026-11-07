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
