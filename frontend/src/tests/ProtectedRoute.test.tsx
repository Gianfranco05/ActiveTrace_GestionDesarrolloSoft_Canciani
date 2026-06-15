import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { ProtectedRoute } from '@/shared/components/ProtectedRoute';
import { AuthProvider, useAuth } from '@/shared/hooks/useAuth';
import { clearLocalStorage, mockUser, setupLocalStorage } from '@/tests/mocks';

function TestChild() {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return null;
  return <div data-testid="protected-content">Contenido protegido</div>;
}

function renderWithRouter(initialEntries: string[]) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route element={<ProtectedRoute />}>
              <Route path="/dashboard" element={<TestChild />} />
            </Route>
            <Route path="/auth/login" element={<div data-testid="login-page">Login</div>} />
          </Routes>
        </AuthProvider>
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

describe('ProtectedRoute', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('redirects to login when not authenticated', async () => {
    renderWithRouter(['/dashboard']);

    await waitFor(() => {
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });
  });

  it('renders children when authenticated', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithRouter(['/dashboard']);

    await waitFor(() => {
      expect(screen.getByTestId('protected-content')).toHaveTextContent('Contenido protegido');
    });
  });

  it('shows loading state during auth check', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    // Never-resolving promise keeps the auth check in loading state
    vi.mocked(mockedAuthService.me).mockReturnValue(new Promise(() => {}));

    renderWithRouter(['/dashboard']);

    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
