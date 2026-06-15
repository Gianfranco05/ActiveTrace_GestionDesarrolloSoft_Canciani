import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { LogAuditoriaPage } from '@/features/admin/pages/LogAuditoriaPage';
import { AuthProvider } from '@/shared/hooks/useAuth';
import { setupLocalStorage, clearLocalStorage } from '@/tests/mocks';

function renderWithProviders() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter initialEntries={['/admin/auditoria/log']}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route path="/admin/auditoria/log" element={<LogAuditoriaPage />} />
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

vi.mock('@/features/admin/services/auditoria.service', () => ({
  getLogAuditoria: vi.fn(),
  getAccionesPorDia: vi.fn(),
  getEstadoComunicaciones: vi.fn(),
  getInteraccionesDocente: vi.fn(),
  getUltimasAcciones: vi.fn(),
}));

const mockLogItems = Array.from({ length: 50 }, (_, i) => ({
  id: String(i + 1),
  fecha_hora: `2026-06-${String(i + 1).padStart(2, '0')}T10:00:00Z`,
  actor_nombre: 'Admin',
  materia_nombre: i % 2 === 0 ? 'Matemáticas' : null,
  accion: ['LOGIN', 'CALIFICAR_ACTUALIZAR', 'LIQUIDACION_CERRAR'][i % 3],
  filas_afectadas: i % 2 === 0 ? 1 : 5,
  ip: '192.168.1.1',
  user_agent: 'Chrome',
}));

describe('LogAuditoriaPage', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('renderiza tabla paginada con datos', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['auditoria:ver'],
    });

    const mockedService = await import('@/features/admin/services/auditoria.service');
    vi.mocked(mockedService.getLogAuditoria).mockResolvedValue({
      items: mockLogItems.slice(0, 50),
      total: 120,
      offset: 0,
      limit: 50,
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Log de Auditoría')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/Página 1 de 3/)).toBeInTheDocument();
    });
  });

  it('navega entre paginas con botones Anterior/Siguiente', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['auditoria:ver'],
    });

    const mockedService = await import('@/features/admin/services/auditoria.service');
    vi.mocked(mockedService.getLogAuditoria).mockResolvedValue({
      items: mockLogItems.slice(0, 50),
      total: 120,
      offset: 0,
      limit: 50,
    });

    const user = userEvent.setup();
    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Siguiente')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Siguiente'));

    await waitFor(() => {
      expect(screen.getByText(/Página 2 de 3/)).toBeInTheDocument();
    });
  });

  it('filtra por accion', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['auditoria:ver'],
    });

    const mockedService = await import('@/features/admin/services/auditoria.service');
    vi.mocked(mockedService.getLogAuditoria).mockResolvedValue({
      items: mockLogItems.slice(0, 50),
      total: 120,
      offset: 0,
      limit: 50,
    });

    const user = userEvent.setup();
    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByLabelText('Acción')).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('Acción'), 'LOGIN');

    await waitFor(() => {
      expect(screen.getByLabelText('Acción')).toHaveValue('LOGIN');
    });
  });

  it('muestra estado vacio cuando no hay datos', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['auditoria:ver'],
    });

    const mockedService = await import('@/features/admin/services/auditoria.service');
    vi.mocked(mockedService.getLogAuditoria).mockResolvedValue({
      items: [], total: 0, offset: 0, limit: 50,
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('No se encontraron registros de auditoría')).toBeInTheDocument();
    });
  });
});
