import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { AuthProvider, useAuth } from '@/shared/hooks/useAuth';
import { mockUser, setupLocalStorage, clearLocalStorage } from '@/tests/mocks';

function TestComponent() {
  const { isAuthenticated, isLoading, user, error, hasPermission } = useAuth();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!isAuthenticated) return <div>Not authenticated</div>;

  return (
    <div>
      <div data-testid="user-name">{user?.name}</div>
      <div data-testid="permission-test">
        {hasPermission('calificaciones:ver') ? 'Has permiso' : 'Sin permiso'}
      </div>
      <div data-testid="no-permission-test">
        {hasPermission('admin:super') ? 'Has admin' : 'Sin admin'}
      </div>
    </div>
  );
}

function renderWithProviders(ui: React.ReactElement, { initialEntries = ['/'] } = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter initialEntries={initialEntries}>
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

const mockedAuthService = await import('@/features/auth/services/auth.service');

describe('AuthContext', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('shows loading initially then unauthenticated when no token', async () => {
    renderWithProviders(<TestComponent />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Not authenticated')).toBeInTheDocument();
    });
  });

  it('hydrates from stored token and shows authenticated state', async () => {
    setupLocalStorage();
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('user-name')).toHaveTextContent('Admin Usuario');
    });

    expect(screen.getByTestId('permission-test')).toHaveTextContent('Has permiso');
    expect(screen.getByTestId('no-permission-test')).toHaveTextContent('Sin admin');
  });

  it('shows unauthenticated when me() returns error', async () => {
    setupLocalStorage();
    vi.mocked(mockedAuthService.me).mockRejectedValue(new Error('Unauthorized'));

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByText('Not authenticated')).toBeInTheDocument();
    });
  });
});

describe('useAuth throws outside provider', () => {
  it('throws error when called outside AuthProvider', () => {
    const queryClient = new QueryClient();

    const renderOutsideProvider = () =>
      render(
        <MemoryRouter>
          <QueryClientProvider client={queryClient}>
            <TestComponent />
          </QueryClientProvider>
        </MemoryRouter>
      );

    expect(renderOutsideProvider).toThrow(
      'useAuth debe usarse dentro de un AuthProvider'
    );
  });
});
