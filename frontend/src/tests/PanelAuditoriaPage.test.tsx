import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { PanelAuditoriaPage } from '@/features/admin/pages/PanelAuditoriaPage';
import { AuthProvider } from '@/shared/hooks/useAuth';
import { setupLocalStorage, clearLocalStorage } from '@/tests/mocks';

function renderWithProviders() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter initialEntries={['/admin/auditoria']}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route path="/admin/auditoria" element={<PanelAuditoriaPage />} />
            <Route path="/admin/auditoria/log" element={<div data-testid="log-page">Log</div>} />
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
  getAccionesPorDia: vi.fn().mockResolvedValue([
    { fecha: '2026-06-01', cantidad: 15 },
    { fecha: '2026-06-02', cantidad: 22 },
  ]),
  getEstadoComunicaciones: vi.fn().mockResolvedValue([
    { docente_id: 'd1', docente_nombre: 'Juan Pérez', pendiente: 3, enviando: 1, enviado: 10, fallido: 0, cancelado: 0 },
  ]),
  getInteraccionesDocente: vi.fn().mockResolvedValue([
    { docente_id: 'd1', docente_nombre: 'Juan Pérez', materia_id: 'm1', materia_nombre: 'Matemáticas', tipo_accion: 'CALIFICAR', cantidad: 25 },
  ]),
  getUltimasAcciones: vi.fn().mockResolvedValue([
    { id: '1', fecha_hora: '2026-06-05T10:00:00Z', usuario_nombre: 'Admin', materia_nombre: null, accion: 'LOGIN', filas_afectadas: 0, ip: '192.168.1.1', user_agent: 'Chrome' },
  ]),
  getLogAuditoria: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 50, total_pages: 0 }),
}));

describe('PanelAuditoriaPage', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('renderiza widgets de metricas', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['auditoria:ver'],
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Panel de Auditoría')).toBeInTheDocument();
    });

    expect(screen.getByText('Acciones por Día')).toBeInTheDocument();
    expect(screen.getByText('Estado de Comunicaciones')).toBeInTheDocument();
    expect(screen.getByText('Interacciones por Docente')).toBeInTheDocument();
    expect(screen.getByText('Últimas Acciones')).toBeInTheDocument();
  });

  it('responde a filtros globales', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['auditoria:ver'],
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByLabelText('Fecha desde')).toBeInTheDocument();
    });

    expect(screen.getByLabelText('Fecha hasta')).toBeInTheDocument();
    expect(screen.getByLabelText('ID Materia')).toBeInTheDocument();
  });
});
