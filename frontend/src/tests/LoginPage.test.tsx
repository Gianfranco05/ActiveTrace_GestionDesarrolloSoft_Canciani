import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { LoginPage } from '@/features/auth/pages/LoginPage';
import { AuthProvider } from '@/shared/hooks/useAuth';
import type { LoginResponse } from '@/shared/types/auth';
import { clearLocalStorage } from '@/tests/mocks';

function renderWithProviders(ui: React.ReactElement, { initialEntries = ['/auth/login'] } = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route path="/auth/login" element={ui} />
            <Route path="/dashboard" element={<div data-testid="dashboard-page">Dashboard</div>} />
            <Route path="/auth/2fa" element={<div data-testid="twofa-page">2FA</div>} />
            <Route path="/auth/forgot" element={<div data-testid="forgot-page">Forgot</div>} />
          </Routes>
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>
  );
}

vi.mock('@/features/auth/services/auth.service', () => ({
  me: vi.fn().mockRejectedValue(new Error('No token')),
  login: vi.fn(),
  logout: vi.fn(),
  verify2FA: vi.fn(),
}));

describe('LoginPage', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('renders login form', async () => {
    renderWithProviders(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeInTheDocument();
    });

    expect(screen.getByText('activia trace')).toBeInTheDocument();
    expect(screen.getByText('Iniciá sesión para continuar')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument();
    expect(screen.getByText('Olvidé mi contraseña')).toBeInTheDocument();
  });

  it('shows validation error for empty fields', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }));

    await waitFor(() => {
      expect(screen.getByText('Email inválido')).toBeInTheDocument();
    });
  });

  it('shows validation error for invalid email', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('Email'), 'invalid-email');
    await user.type(screen.getByLabelText('Contraseña'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }));

    await waitFor(() => {
      expect(screen.getByText('Email inválido')).toBeInTheDocument();
    });
  });

  it('shows error message on failed login', async () => {
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.login).mockRejectedValue({
      response: { status: 401 },
    });

    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('Email'), 'user@test.com');
    await user.type(screen.getByLabelText('Contraseña'), 'wrong-password');
    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }));

    await waitFor(() => {
      expect(screen.getByText('Credenciales inválidas')).toBeInTheDocument();
    });
  });

  it('redirects to /dashboard on successful login without 2FA', async () => {
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.login).mockResolvedValue({
      access_token: 'token',
      refresh_token: 'refresh',
      requires_2fa: false,
      user: {
        id: '1',
        email: 'user@test.com',
        name: 'Test User',
        roles: ['admin'],
        permissions: [],
      },
    });
    // me() is called after login to hydrate the user; must resolve here
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1',
      email: 'user@test.com',
      name: 'Test User',
      roles: ['admin'],
      permissions: [],
    });

    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('Email'), 'user@test.com');
    await user.type(screen.getByLabelText('Contraseña'), 'password');
    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }));

    await waitFor(() => {
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });
  });

  it('redirects to /auth/2fa when 2FA is required', async () => {
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.login).mockResolvedValue({
      requires_2fa: true,
      temp_token: 'temp-token',
      access_token: '',
      refresh_token: '',
    });

    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('Email'), 'user@test.com');
    await user.type(screen.getByLabelText('Contraseña'), 'password');
    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }));

    await waitFor(() => {
      expect(screen.getByTestId('twofa-page')).toBeInTheDocument();
    });
  });

  it('shows loading state on submit', async () => {
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    // The promise never resolves during this test — we only check the loading state
    let resolveLogin: (value: LoginResponse) => void;
    const loginPromise = new Promise<LoginResponse>((resolve) => {
      resolveLogin = resolve;
    });
    vi.mocked(mockedAuthService.login).mockReturnValue(loginPromise);

    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('Email'), 'user@test.com');
    await user.type(screen.getByLabelText('Contraseña'), 'password');
    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }));

    expect(screen.getByRole('button', { name: /iniciando sesión/i })).toBeDisabled();

    // Resolve to allow test cleanup
    resolveLogin!({ access_token: 't', refresh_token: 'r', requires_2fa: false, user: { id: '1', email: 'x@x.com', name: 'X', roles: [], permissions: [] } });
  });
});
