import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { RequirePermission } from '@/shared/components/RequirePermission';
import { AuthProvider } from '@/shared/hooks/useAuth';
import { clearLocalStorage, setupLocalStorage, mockUser } from '@/tests/mocks';

vi.mock('@/features/auth/services/auth.service', () => ({
  me: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  verify2FA: vi.fn(),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>{ui}</AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>
  );
}

describe('Route Guards', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('renders content when user has calificaciones:importar permission', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(
      <Routes>
        <Route
          path="/"
          element={
            <RequirePermission requiredPermission="calificaciones:importar">
              <div data-testid="importar-content">Importar Calificaciones</div>
            </RequirePermission>
          }
        />
      </Routes>
    );

    await waitFor(() => {
      expect(screen.getByTestId('importar-content')).toHaveTextContent('Importar Calificaciones');
    });
  });

  it('shows 403 fallback when user lacks atrasados:ver permission', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(
      <RequirePermission requiredPermission="atrasados:ver">
        <div data-testid="atrasados-content">Atrasados</div>
      </RequirePermission>
    );

    await waitFor(() => {
      expect(screen.getByText('No tenés permisos para acceder a esta sección')).toBeInTheDocument();
    });
  });

  it('renders content when user has comunicacion:enviar permission', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(
      <Routes>
        <Route
          path="/"
          element={
            <RequirePermission requiredPermission="comunicacion:enviar">
              <div data-testid="comunicaciones-content">Comunicaciones</div>
            </RequirePermission>
          }
        />
      </Routes>
    );

    await waitFor(() => {
      expect(screen.getByTestId('comunicaciones-content')).toHaveTextContent('Comunicaciones');
    });
  });
});
