import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { RequirePermission } from '@/shared/components/RequirePermission';
import { AuthProvider } from '@/shared/hooks/useAuth';
import { setupLocalStorage, clearLocalStorage, mockUser } from '@/tests/mocks';

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>{ui}</AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>
  );
}

vi.mock('@/features/auth/services/auth.service', () => ({
  me: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  verify2FA: vi.fn(),
}));

describe('RequirePermission', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('renders children when user has the required permission', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(
      <RequirePermission requiredPermission="calificaciones:ver">
        <div data-testid="permitted-content">Contenido con permiso</div>
      </RequirePermission>
    );

    await waitFor(() => {
      expect(screen.getByTestId('permitted-content')).toHaveTextContent('Contenido con permiso');
    });
  });

  it('shows 403 fallback when user lacks permission', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(
      <RequirePermission requiredPermission="admin:super">
        <div data-testid="permitted-content">Contenido con permiso</div>
      </RequirePermission>
    );

    await waitFor(() => {
      expect(screen.getByText('No tenés permisos para acceder a esta sección')).toBeInTheDocument();
    });
  });

  it('renders children when requiredPermission is null', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(
      <RequirePermission requiredPermission={null}>
        <div data-testid="public-content">Contenido público</div>
      </RequirePermission>
    );

    await waitFor(() => {
      expect(screen.getByTestId('public-content')).toHaveTextContent('Contenido público');
    });
  });
});
