import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
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
            <Route path="/finanzas/liquidaciones/historial" element={<div data-testid="historial-page">Historial</div>} />
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
  getLiquidaciones: vi.fn().mockResolvedValue([]),
  getLiquidacionKPI: vi.fn().mockResolvedValue({ total_general: 100000, total_sin_factura: 70000, total_nexo: 30000, total_facturantes: 1, total_docentes: 5 }),
  cerrarLiquidacion: vi.fn(),
  getHistorialLiquidaciones: vi.fn().mockResolvedValue([]),
}));

vi.mock('@/features/admin/services/estructura.service', () => ({
  getCarreras: vi.fn().mockResolvedValue([{ id: '1', codigo: 'ING', nombre: 'Ingeniería', activa: true }]),
  getCohortes: vi.fn().mockResolvedValue([]),
  getMaterias: vi.fn().mockResolvedValue([]),
  createCarrera: vi.fn(),
  createCohorte: vi.fn(),
  createMateria: vi.fn(),
  updateCarrera: vi.fn(),
  toggleCarreraEstado: vi.fn(),
  toggleCohorteEstado: vi.fn(),
  toggleMateriaEstado: vi.fn(),
}));

describe('LiquidacionesPage', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('renderiza KPIs de cabecera', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['liquidaciones:ver', 'liquidaciones:cerrar'],
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Total General')).toBeInTheDocument();
    });

    expect(screen.getByText('Total NEXO')).toBeInTheDocument();
    expect(screen.getByText('Total sin Factura')).toBeInTheDocument();
    expect(screen.getByText('Docentes', { exact: false })).toBeInTheDocument();
  });

  it('renderiza tabs de segmentación General/NEXO/Factura', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['liquidaciones:ver'],
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('General')).toBeInTheDocument();
    });

    expect(screen.getByText('NEXO')).toBeInTheDocument();
    expect(screen.getByText('Factura')).toBeInTheDocument();
  });

  it('renderiza filtros de cohorte y mes', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['liquidaciones:ver'],
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByLabelText('Cohorte')).toBeInTheDocument();
    });

    expect(screen.getByLabelText('Mes')).toBeInTheDocument();
  });

  it('muestra boton Cerrar Liquidacion solo con permiso', async () => {
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

  it('oculta boton Cerrar Liquidacion sin permiso', async () => {
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
});
