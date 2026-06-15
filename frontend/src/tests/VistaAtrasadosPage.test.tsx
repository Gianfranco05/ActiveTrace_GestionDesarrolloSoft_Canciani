import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { VistaAtrasadosPage } from '@/features/academico/pages/VistaAtrasadosPage';
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

vi.mock('@/features/academico/services/analisis.service', () => ({
  getAtrasados: vi.fn(),
  getRanking: vi.fn(),
  getNotasFinales: vi.fn(),
  getReportesRapidos: vi.fn(),
  getMonitores: vi.fn(),
  uploadReporteFinalizacion: vi.fn(),
  getEntregasSinCorregir: vi.fn(),
  exportEntregasSinCorregir: vi.fn(),
  exportNotasFinales: vi.fn(),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <MemoryRouter initialEntries={['/academico/atrasados']}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route path="/academico/atrasados" element={ui} />
          </Routes>
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>
  );
}

describe('VistaAtrasadosPage', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('renders page title', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(<VistaAtrasadosPage />);

    await waitFor(() => {
      expect(screen.getByText('Alumnos Atrasados')).toBeInTheDocument();
    });
  });

  it('shows prompt to select materia when none selected', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    renderWithProviders(<VistaAtrasadosPage />);

    await waitFor(() => {
      expect(screen.getByText('Seleccioná una materia para ver los alumnos atrasados')).toBeInTheDocument();
    });
  });

  it('renders materia selector', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue(mockUser);

    const mockedApi = await import('@/shared/services/api');
    vi.mocked(mockedApi.default.get).mockResolvedValue({ data: [] });

    renderWithProviders(<VistaAtrasadosPage />);

    await waitFor(() => {
      expect(screen.getByText('Materia')).toBeInTheDocument();
    });
  });
});
