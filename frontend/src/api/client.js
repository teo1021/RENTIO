import { getToken, logout } from '../store/auth.js';

const baseURL = (import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(message, status = 0, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export async function request(path, options = {}) {
  const controller = new AbortController();
  const { timeout: timeoutMs = 30000, ...fetchOptions } = options;
  const timeout = window.setTimeout(
    () => controller.abort(),
    timeoutMs,
  );
  const headers = new Headers(options.headers || {});
  const token = getToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);

  let body = options.body;
  if (body && !(body instanceof FormData) && typeof body !== 'string') {
    headers.set('Content-Type', 'application/json');
    body = JSON.stringify(body);
  }

  try {
    const response = await fetch(`${baseURL}${path}`, {
      ...fetchOptions,
      body,
      headers,
      signal: controller.signal,
    });
    const payload = await response.json().catch(() => null);
    if (response.status === 401 && getToken()) {
      logout();
      window.dispatchEvent(new CustomEvent('rentio:unauthorized'));
    }
    if (!response.ok || payload?.success === false) {
      const error = payload?.error || {};
      throw new ApiError(
        error.message || payload?.message || `Error HTTP ${response.status}`,
        response.status,
        error.details,
      );
    }
    return payload?.data !== undefined ? payload.data : payload;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error.name === 'AbortError') {
      throw new ApiError('La solicitud tardó demasiado. Inténtalo de nuevo.');
    }
    throw new ApiError('No fue posible conectar con el servidor RENTIO.');
  } finally {
    window.clearTimeout(timeout);
  }
}

export function apiError(error, fallback = 'Ocurrió un error. Inténtalo de nuevo.') {
  if (error instanceof ApiError) {
    const details = error.details;
    if (details && typeof details === 'object') {
      const first = Object.values(details)
        .flatMap((value) => Array.isArray(value) ? value : [value])[0];
      if (typeof first === 'string') return first;
    }
    return error.message || fallback;
  }
  return error instanceof Error ? error.message : fallback;
}
