import axios, { AxiosError } from 'axios';
import { useAuthStore } from '../store/authStore';

// The Flask API is the public entry point. The FastAPI AI service is internal
// and must never be called directly from the browser.
const baseURL = (import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1').replace(/\/$/, '');

export const api = axios.create({
  baseURL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error?: { message?: string; details?: unknown }; message?: string }>) => {
    if (error.response?.status === 401 && useAuthStore.getState().token) {
      useAuthStore.getState().logout();
      if (window.location.pathname !== '/login') window.location.assign('/login?expired=1');
    }
    return Promise.reject(error);
  },
);

export function getApiError(error: unknown, fallback = 'Ocurrió un error. Inténtalo de nuevo.') {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { error?: { message?: string; details?: unknown }; message?: string } | undefined;
    const message = data?.error?.message || data?.message || error.message;
    const details = data?.error?.details;
    if (details && typeof details === 'object') {
      const first = Object.values(details as Record<string, unknown>).flatMap((value) =>
        Array.isArray(value) ? value : [value],
      )[0];
      if (typeof first === 'string') return first;
    }
    return message || fallback;
  }
  return error instanceof Error ? error.message : fallback;
}
