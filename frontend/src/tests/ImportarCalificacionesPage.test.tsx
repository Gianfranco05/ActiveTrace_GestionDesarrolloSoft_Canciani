import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { ImportarCalificacionesPage } from '@/features/academico/pages/ImportarCalificacionesPage';
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

vi.mock('@/features/academico/services/calificaciones.service', () => ({
  uploadCalificaciones: vi.fn(),
  getPreview: vi.fn(),
  confirmarImportacion: vi.fn(),
  getUmbral: vi.fn(),
  setUmbral: vi.fn(),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <MemoryRouter initialEntries={['/academico/importar']}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route path="/academico/importar" element={ui} />
          </Routes>
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>
  );
}

describe('ImportarCalificacionesPage', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('renders the page title', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(<ImportarCalificacionesPage />);

    await waitFor(() => {
      expect(screen.getByText('Importar Calificaciones')).toBeInTheDocument();
    });
  });

  it('shows materia selector', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    const mockedApi = await import('@/shared/services/api');
    vi.mocked(mockedApi.default.get).mockResolvedValue({ data: [] });

    renderWithProviders(<ImportarCalificacionesPage />);

    await waitFor(() => {
      expect(screen.getByText('Materia')).toBeInTheDocument();
    });
  });

  it('shows prompt to select a materia', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(<ImportarCalificacionesPage />);

    await waitFor(() => {
      expect(screen.getByText('Seleccioná una materia para empezar')).toBeInTheDocument();
    });
  });
});
