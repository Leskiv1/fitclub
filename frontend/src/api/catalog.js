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

export async function fetchHalls() {
  const { data } = await apiClient.get('/halls', ALL);
  return data.items;
}

export async function fetchSettings() {
  const { data } = await apiClient.get('/settings');
  return data;
}

// --- Admin (ЗВ-7): create with POST, change with PATCH, remove with DELETE ---

function crud(path) {
  return {
    async save(id, payload) {
      const { data } = id
        ? await apiClient.patch(`${path}/${id}`, payload)
        : await apiClient.post(path, payload);
      return data;
    },
    async remove(id) {
      await apiClient.delete(`${path}/${id}`);
    },
  };
}

export const tariffsApi = crud('/tariffs');
export const optionsApi = crud('/membership-options');
export const hallsApi = crud('/halls');
export const trainersApi = crud('/trainers');

// Prototype on the server: an inactive copy of the tariff to edit
export async function cloneTariff(tariffId) {
  const { data } = await apiClient.post(`/tariffs/${tariffId}/clone`);
  return data;
}

export async function updateSettings(payload) {
  const { data } = await apiClient.patch('/settings', payload);
  return data;
}

export async function fetchTrainer(trainerId) {
  const { data } = await apiClient.get(`/trainers/${trainerId}`);
  return data;
}

export async function fetchTrainerClients(trainerId) {
  const { data } = await apiClient.get(`/trainers/${trainerId}/clients`);
  return data;
}
