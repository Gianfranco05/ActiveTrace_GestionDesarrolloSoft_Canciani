import {
  createContext,
  useContext,
  useReducer,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react';
import { useNavigate } from 'react-router-dom';

import * as authService from '@/features/auth/services/auth.service';
import { TEMP_TOKEN_KEY } from '@/shared/utils/auth-constants';
import { onForceLogout } from '@/shared/utils/auth-events';
import {
  setAccessToken,
  setRefreshToken,
  clearAuthTokens,
  getAccessToken,
} from '@/shared/utils/storage';

import type { AuthState, AuthAction, LoginResult } from '@/shared/types/auth';

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_LOADING':
      return { ...state, isLoading: true, error: null };
    case 'AUTH_SUCCESS':
      return {
        user: action.user,
        isLoading: false,
        isAuthenticated: true,
        error: null,
        permissions: action.permissions,
        roles: action.roles,
      };
    case 'AUTH_UNAUTHENTICATED':
      return {
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null,
        permissions: [],
        roles: [],
      };
    case 'AUTH_ERROR':
      return { ...state, isLoading: false, error: action.error };
    case 'AUTH_CLEAR_ERROR':
      return { ...state, error: null };
    case 'AUTH_LOGOUT':
      return {
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null,
        permissions: [],
        roles: [],
      };
    default:
      return state;
  }
}

const initialState: AuthState = {
  user: null,
  isLoading: true,
  isAuthenticated: false,
  error: null,
  permissions: [],
  roles: [],
};

export interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<LoginResult>;
  verify2FA: (code: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (perm: string) => boolean;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const navigate = useNavigate();

  useEffect(() => {
    const unsubscribe = onForceLogout(() => {
      clearAuthTokens();
      dispatch({ type: 'AUTH_LOGOUT' });
      navigate('/auth/login', { replace: true });
    });

    return unsubscribe;
  }, [navigate]);

  useEffect(() => {
    const init = async () => {
      const token = getAccessToken();
      if (!token) {
        await new Promise((resolve) => setTimeout(resolve, 0));
        dispatch({ type: 'AUTH_UNAUTHENTICATED' });
        return;
      }

      dispatch({ type: 'AUTH_LOADING' });
      try {
        const user = await authService.me();
        dispatch({
          type: 'AUTH_SUCCESS',
          user,
          permissions: user.permissions,
          roles: user.roles,
        });
      } catch {
        dispatch({ type: 'AUTH_UNAUTHENTICATED' });
      }
    };

    init();
  }, []);

  const login = useCallback(
    async (email: string, password: string): Promise<LoginResult> => {
      dispatch({ type: 'AUTH_LOADING' });
      try {
        const response = await authService.login(email, password);

        if (response.requires_2fa && response.temp_token) {
          dispatch({ type: 'AUTH_CLEAR_ERROR' });
          return { requires_2fa: true };
        }

        if (response.access_token && response.refresh_token) {
          setAccessToken(response.access_token);
          setRefreshToken(response.refresh_token);
          const user = await authService.me();
          dispatch({
            type: 'AUTH_SUCCESS',
            user,
            permissions: user.permissions,
            roles: user.roles,
          });
        }

        return { requires_2fa: false };
      } catch (err) {
        const message =
          axiosError(err) === 401
            ? 'Credenciales inválidas'
            : 'Error de conexión. Intentá de nuevo.';
        dispatch({ type: 'AUTH_ERROR', error: message });
        throw new Error(message);
      }
    },
    []
  );

  const verify2FA = useCallback(async (code: string) => {
    dispatch({ type: 'AUTH_LOADING' });
    try {
      const tempToken = sessionStorage.getItem(TEMP_TOKEN_KEY);
      if (!tempToken) {
        throw new Error('No hay sesión pendiente de 2FA');
      }

      const response = await authService.verify2FA(tempToken, code);

      setAccessToken(response.access_token);
      setRefreshToken(response.refresh_token);
      sessionStorage.removeItem(TEMP_TOKEN_KEY);

      dispatch({
        type: 'AUTH_SUCCESS',
        user: response.user,
        permissions: response.user.permissions,
        roles: response.user.roles,
      });
    } catch (err) {
      const message =
        axiosError(err) === 401
          ? 'Código inválido'
          : 'Error de verificación. Intentá de nuevo.';
      dispatch({ type: 'AUTH_ERROR', error: message });
      throw new Error(message);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch {
      // Always clear local state even if API call fails
    }
    clearAuthTokens();
    dispatch({ type: 'AUTH_LOGOUT' });
    navigate('/auth/login', { replace: true });
  }, [navigate]);

  const hasPermission = useCallback(
    (perm: string): boolean => {
      if (!state.isAuthenticated || !state.user) return false;
      return state.permissions.includes(perm);
    },
    [state.isAuthenticated, state.permissions, state.user]
  );

  const value: AuthContextValue = {
    ...state,
    login,
    verify2FA,
    logout,
    hasPermission,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  return context;
}

export function useCurrentUser() {
  const { user, isLoading } = useAuth();
  return { user, isLoading };
}

export function usePermission(perm: string): boolean {
  const { hasPermission } = useAuth();
  return hasPermission(perm);
}

function axiosError(err: unknown): number | null {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response: { status: number } }).response;
    return response?.status ?? null;
  }
  return null;
}
