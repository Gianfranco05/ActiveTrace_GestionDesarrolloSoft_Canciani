import api from '@/shared/services/api';
import { getRefreshToken } from '@/shared/utils/storage';

import type { LoginResponse, TwoFactorResponse, RefreshResponse, User } from '@/shared/types/auth';

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post('/auth/login', { email, password });
  return data;
}

export async function verify2FA(sessionToken: string, code: string): Promise<TwoFactorResponse> {
  const { data } = await api.post('/auth/2fa/verify-login', {
    session_token: sessionToken,
    totp_code: code,
  });
  return data;
}

export async function refreshToken(token: string): Promise<RefreshResponse> {
  const { data } = await api.post('/auth/refresh', { refresh_token: token });
  return data;
}

export async function logout(): Promise<void> {
  const refreshTokenValue = getRefreshToken();
  if (refreshTokenValue) {
    await api.post('/auth/logout', { refresh_token: refreshTokenValue });
  }
}

export async function forgotPassword(email: string): Promise<void> {
  await api.post('/auth/forgot', { email });
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  await api.post('/auth/reset', { token, new_password: newPassword });
}

export async function me(): Promise<User> {
  const { data } = await api.get('/auth/me');
  return {
    id: data.id,
    email: data.email,
    name: `${data.nombre} ${data.apellidos}`,
    roles: data.roles,
    permissions: data.permissions,
  };
}
