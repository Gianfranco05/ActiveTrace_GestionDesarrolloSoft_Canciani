import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { GrillaSalarialPage } from '@/features/finanzas/pages/GrillaSalarialPage';
import { AuthProvider } from '@/shared/hooks/useAuth';
import { setupLocalStorage, clearLocalStorage } from '@/tests/mocks';

function renderWithProviders() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter initialEntries={['/finanzas/grilla-salarial']}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route path="/finanzas/grilla-salarial" element={<GrillaSalarialPage />} />
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

vi.mock('@/features/finanzas/services/salario.service', () => ({
  getSalariosBase: vi.fn().mockResolvedValue([
    { id: '1', rol: 'Profesor', monto: 50000, desde: '2026-01-01', hasta: null, activo: true },
  ]),
  createSalarioBase: vi.fn(),
  updateSalarioBase: vi.fn(),
  deleteSalarioBase: vi.fn(),
  getSalariosPlus: vi.fn().mockResolvedValue([
    { id: '1', grupo: 'A', rol: 'Profesor', descripcion: 'Antigüedad', monto: 10000, desde: '2026-01-01', hasta: null, activo: true },
  ]),
  createSalarioPlus: vi.fn(),
  updateSalarioPlus: vi.fn(),
  deleteSalarioPlus: vi.fn(),
}));

describe('GrillaSalarialPage', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('renderiza tabla de SalarioBase con datos', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['liquidaciones:configurar-salarios'],
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Grilla Salarial')).toBeInTheDocument();
    });

    expect(screen.getByText('Salario Base')).toBeInTheDocument();
    expect(screen.getByText('Salario Plus')).toBeInTheDocument();
  });

  it('renderiza formularios de SalarioBase y SalarioPlus', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['liquidaciones:configurar-salarios'],
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Nuevo Salario Base')).toBeInTheDocument();
    });

    expect(screen.getByText('Nuevo Salario Plus')).toBeInTheDocument();
  });

  it('crea un SalarioBase via formulario', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['liquidaciones:configurar-salarios'],
    });

    const user = userEvent.setup();
    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByLabelText('Rol')).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('Rol'), 'Tutor');
    const montoInput = screen.getByLabelText('Monto');
    await user.clear(montoInput);
    await user.type(montoInput, '35000');
    await user.type(screen.getByLabelText('Desde'), '2026-06-01');
    await user.click(screen.getAllByText('Crear Salario Base')[0]);

    const mockedService = await import('@/features/finanzas/services/salario.service');
    expect(mockedService.createSalarioBase).toHaveBeenCalled();
  });
});
