import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { ComunicacionesPage } from '@/features/academico/pages/ComunicacionesPage';
import { AuthProvider } from '@/shared/hooks/useAuth';
import { clearLocalStorage, setupLocalStorage, mockUser } from '@/tests/mocks';

vi.mock('@/features/auth/services/auth.service', () => ({
  me: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  verify2FA: vi.fn(),
}));

vi.mock('@/shared/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

vi.mock('@/features/academico/services/comunicaciones.service', () => ({
  getPreview: vi.fn(),
  enviarComunicacion: vi.fn(),
  getEstadoComunicaciones: vi.fn(),
  cancelarComunicacion: vi.fn(),
}));

function renderWithProviders(ui: React.ReactElement, initialEntries: string[] = ['/academico/comunicaciones']) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route path="/academico/comunicaciones" element={ui} />
            <Route path="/academico/atrasados" element={<div data-testid="atrasados-page">Atrasados</div>} />
          </Routes>
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>
  );
}

describe('ComunicacionesPage', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('shows message when no alumnos selected', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(<ComunicacionesPage />);

    await waitFor(() => {
      expect(screen.getByText('No hay alumnos seleccionados para comunicar.')).toBeInTheDocument();
    });
  });

  it('shows go back to atrasados button when no alumnos selected', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(<ComunicacionesPage />);

    await waitFor(() => {
      expect(screen.getByText('Ir a Atrasados')).toBeInTheDocument();
    });
  });

  it('renders preview view when alumnos are selected', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(
      <ComunicacionesPage />,
      ['/academico/comunicaciones?alumnosIds=alumno-1,alumno-2&materiaId=mat-1']
    );

    await waitFor(() => {
      expect(screen.getByText(/Previsualizá y confirmá/i)).toBeInTheDocument();
    });
  });
});
