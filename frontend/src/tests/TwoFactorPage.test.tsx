import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { TwoFactorPage } from '@/features/auth/pages/TwoFactorPage';
import { AuthProvider } from '@/shared/hooks/useAuth';
import { TEMP_TOKEN_KEY } from '@/shared/utils/auth-constants';
import type { TwoFactorResponse } from '@/shared/types/auth';
import { clearLocalStorage } from '@/tests/mocks';

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter initialEntries={['/auth/2fa']}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>{ui}</AuthProvider>
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

describe('TwoFactorPage', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
    sessionStorage.setItem(TEMP_TOKEN_KEY, 'test-temp-token');
  });

  it('renders 2FA form', async () => {
    renderWithProviders(<TwoFactorPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Verificar' })).toBeInTheDocument();
    });

    expect(screen.getByText('Verificación en dos pasos')).toBeInTheDocument();
    expect(
      screen.getByText('Ingresá el código de verificación de tu aplicación de autenticación')
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Código de verificación')).toBeInTheDocument();
    expect(screen.getByText('Volver al inicio de sesión')).toBeInTheDocument();
  });

  it('shows validation error for incomplete code', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TwoFactorPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Verificar' })).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('Código de verificación'), '123');
    await user.click(screen.getByRole('button', { name: 'Verificar' }));

    await waitFor(() => {
      expect(screen.getByText('El código debe tener 6 dígitos')).toBeInTheDocument();
    });
  });

  it('shows error message on failed verification', async () => {
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.verify2FA).mockRejectedValue({
      response: { status: 401 },
    });

    const user = userEvent.setup();
    renderWithProviders(<TwoFactorPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Verificar' })).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('Código de verificación'), '123456');
    await user.click(screen.getByRole('button', { name: 'Verificar' }));

    await waitFor(() => {
      expect(screen.getByText('Código inválido')).toBeInTheDocument();
    });
  });

  it('shows loading state during verification', async () => {
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    // The promise never resolves during this test — we only check the loading state
    let resolveVerify: (value: TwoFactorResponse) => void;
    const verifyPromise = new Promise<TwoFactorResponse>((resolve) => {
      resolveVerify = resolve;
    });
    vi.mocked(mockedAuthService.verify2FA).mockReturnValue(verifyPromise);

    const user = userEvent.setup();
    renderWithProviders(<TwoFactorPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Verificar' })).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('Código de verificación'), '123456');
    await user.click(screen.getByRole('button', { name: 'Verificar' }));

    expect(screen.getByRole('button', { name: /verificando/i })).toBeDisabled();

    // Resolve to allow test cleanup
    resolveVerify!({ access_token: 't', refresh_token: 'r', user: { id: '1', email: 'x@x.com', name: 'X', roles: [], permissions: [] } });
  });
});
