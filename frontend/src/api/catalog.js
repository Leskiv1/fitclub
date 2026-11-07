import apiClient from './client';

// The catalog is public: guests see tariffs, trainers and club hours on the landing page.
// Lists are small, so one page of 100 is the whole catalog.
const ALL = { params: { limit: 100 } };

export async function fetchTariffs() {
  const { data } = await apiClient.get('/tariffs', ALL);
  return data.items;
}

export async function fetchOptions() {
  const { data } = await apiClient.get('/membership-options', ALL);
  return data.items;
}

export async function fetchTrainers() {
  const { data } = await apiClient.get('/trainers', ALL);
  return data.items;
}

export async function fetchSettings() {
  const { data } = await apiClient.get('/settings');
  return data;
}
