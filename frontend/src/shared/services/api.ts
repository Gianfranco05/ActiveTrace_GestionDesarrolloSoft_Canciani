import axios from 'axios';
import { toast } from 'sonner';

import { AuthEvents, AUTH_EVENTS } from '@/shared/utils/auth-events';
import { getAccessToken, getRefreshToken, setAccessToken, setRefreshToken, clearAuthTokens } from '@/shared/utils/storage';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let pendingQueue: Array<{
  resolve: () => void;
  reject: (error: unknown) => void;
}> = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // ── Show toast for API errors (skip auth endpoints) ──
    const skipToast = originalRequest?.url?.includes('/auth/');
    if (!skipToast && error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail;

      if (status === 422) {
        const msg = Array.isArray(detail)
          ? detail.map((d: any) => d.msg || d.message).filter(Boolean).join('. ')
          : (detail || 'Datos inválidos. Revisá los campos.');
        toast.error(msg);
      } else if (status === 500) {
        toast.error(detail || 'Error interno del servidor. Reintentá más tarde.');
      } else if (status === 404) {
        // Silent for GET 404 — normal when resources don't exist yet
        if (originalRequest?.method?.toLowerCase() !== 'get') {
          toast.error(detail || 'Recurso no encontrado.');
        }
      }
    } else if (!error.response) {
      toast.error('No se pudo conectar con el servidor. ¿Está corriendo el backend?');
    }

    // ── 401 token refresh logic ──
    if (
      !error.response ||
      error.response.status !== 401 ||
      originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/refresh')
    ) {
      return Promise.reject(error);
    }

    if (!isRefreshing) {
      isRefreshing = true;

      try {
        const refreshToken = getRefreshToken();
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        const { data } = await axios.post(
          `${api.defaults.baseURL ?? ''}/auth/refresh`,
          { refresh_token: refreshToken }
        );

        setAccessToken(data.access_token);
        if (data.refresh_token) {
          setRefreshToken(data.refresh_token);
        }

        pendingQueue.forEach(({ resolve }) => resolve());
        pendingQueue = [];

        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        pendingQueue.forEach(({ reject }) => reject(refreshError));
        pendingQueue = [];
        clearAuthTokens();
        AuthEvents.emit(AUTH_EVENTS.FORCE_LOGOUT);
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return new Promise((resolve, reject) => {
      pendingQueue.push({
        resolve: () => {
          originalRequest.headers.Authorization = `Bearer ${getAccessToken()}`;
          resolve(api(originalRequest));
        },
        reject,
      });
    });
  }
);

export default api;
