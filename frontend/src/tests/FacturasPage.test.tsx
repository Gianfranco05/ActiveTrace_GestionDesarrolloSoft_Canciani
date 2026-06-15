import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { FacturasPage } from '@/features/finanzas/pages/FacturasPage';
import { AuthProvider } from '@/shared/hooks/useAuth';
import { setupLocalStorage, clearLocalStorage } from '@/tests/mocks';

function renderWithProviders() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter initialEntries={['/finanzas/facturas']}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route path="/finanzas/facturas" element={<FacturasPage />} />
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

vi.mock('@/features/finanzas/services/factura.service', () => ({
  getFacturas: vi.fn(),
  createFactura: vi.fn(),
  cambiarEstadoFactura: vi.fn(),
}));

describe('FacturasPage', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('renderiza tabla de facturas con datos', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['facturas:gestionar'],
    });

    const mockedService = await import('@/features/finanzas/services/factura.service');
    vi.mocked(mockedService.getFacturas).mockResolvedValue([
      { id: '1', docente_id: 'd1', docente_nombre: 'Juan Pérez', periodo: '2026-06', detalle: 'Honorarios junio', archivo_nombre: 'factura.pdf', archivo_tamano: 102400, estado: 'Pendiente', fecha_carga: '2026-06-01', fecha_abono: null },
      { id: '2', docente_id: 'd2', docente_nombre: 'María García', periodo: '2026-05', detalle: 'Honorarios mayo', archivo_nombre: 'factura2.pdf', archivo_tamano: 204800, estado: 'Abonada', fecha_carga: '2026-05-15', fecha_abono: '2026-06-01' },
    ]);

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Facturas')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Juan Pérez')).toBeInTheDocument();
    });
    expect(screen.getByText('María García')).toBeInTheDocument();
  });

  it('muestra formulario de carga al hacer click en Nueva Factura', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['facturas:gestionar'],
    });

    const mockedService = await import('@/features/finanzas/services/factura.service');
    vi.mocked(mockedService.getFacturas).mockResolvedValue([]);

    const user = userEvent.setup();
    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Nueva Factura')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Nueva Factura'));

    expect(screen.getByText('Cargar Factura')).toBeInTheDocument();
  });

  it('permite filtrar por estado', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['facturas:gestionar'],
    });

    const mockedService = await import('@/features/finanzas/services/factura.service');
    vi.mocked(mockedService.getFacturas).mockResolvedValue([]);

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByLabelText('Estado')).toBeInTheDocument();
    });
  });
});
