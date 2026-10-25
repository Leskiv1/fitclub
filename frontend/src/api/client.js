import axios from 'axios';

// All requests go to /api; in development Vite proxies them to the FastAPI server
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

export default apiClient;
