export interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
  permissions: string[];
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  requires_2fa: boolean;
  user?: User;
  temp_token?: string;
}

export interface LoginResult {
  requires_2fa: boolean;
}

export interface TwoFactorResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface RefreshResponse {
  access_token: string;
  refresh_token: string;
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  permissions: string[];
  roles: string[];
}

export type AuthAction =
  | { type: 'AUTH_LOADING' }
  | { type: 'AUTH_SUCCESS'; user: User; permissions: string[]; roles: string[] }
  | { type: 'AUTH_UNAUTHENTICATED' }
  | { type: 'AUTH_ERROR'; error: string }
  | { type: 'AUTH_CLEAR_ERROR' }
  | { type: 'AUTH_LOGOUT' };
