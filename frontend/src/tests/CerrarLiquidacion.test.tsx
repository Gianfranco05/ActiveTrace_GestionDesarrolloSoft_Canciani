import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { LiquidacionesPage } from '@/features/finanzas/pages/LiquidacionesPage';
import { AuthProvider } from '@/shared/hooks/useAuth';
import { setupLocalStorage, clearLocalStorage } from '@/tests/mocks';

function renderWithProviders() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter initialEntries={['/finanzas/liquidaciones']}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route path="/finanzas/liquidaciones" element={<LiquidacionesPage />} />
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

vi.mock('@/features/finanzas/services/liquidacion.service', () => ({
  getLiquidaciones: vi.fn(),
  getLiquidacionKPI: vi.fn(),
  cerrarLiquidacion: vi.fn(),
  getHistorialLiquidaciones: vi.fn(),
}));

vi.mock('@/features/admin/services/estructura.service', () => ({
  getCarreras: vi.fn(),
  getCohortes: vi.fn(),
  getMaterias: vi.fn(),
  createCarrera: vi.fn(),
  createCohorte: vi.fn(),
  createMateria: vi.fn(),
  updateCarrera: vi.fn(),
  toggleCarreraEstado: vi.fn(),
  toggleCohorteEstado: vi.fn(),
  toggleMateriaEstado: vi.fn(),
}));

describe('Cerrar Liquidacion', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('boton de cierre requiere permiso liquidaciones:cerrar', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['liquidaciones:ver'],
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.queryByText('Cerrar Liquidación')).not.toBeInTheDocument();
    });
  });

  it('boton de cierre visible con permiso', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['liquidaciones:ver', 'liquidaciones:cerrar'],
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Cerrar Liquidación')).toBeInTheDocument();
    });
  });

  it('muestra dialogo de confirmacion antes de cerrar', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['liquidaciones:ver', 'liquidaciones:cerrar'],
    });

    const mockedEstructura = await import('@/features/admin/services/estructura.service');
    vi.mocked(mockedEstructura.getCarreras).mockResolvedValue([{ id: '1', codigo: 'ING', nombre: 'Ingeniería', activa: true }]);

    const user = userEvent.setup();
    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Cerrar Liquidación')).toBeInTheDocument();
    });

    await user.selectOptions(screen.getByLabelText('Cohorte'), '1');
    await user.selectOptions(screen.getByLabelText('Mes'), '06');

    const btn = screen.getByText('Cerrar Liquidación');
    expect(btn.closest('button')).not.toBeDisabled();

    await user.click(btn);

    await waitFor(() => {
      expect(screen.getByText('¿Estás seguro de que querés cerrar esta liquidación?')).toBeInTheDocument();
    });

    expect(screen.getByText('Esta acción es irreversible.')).toBeInTheDocument();
  });
});
