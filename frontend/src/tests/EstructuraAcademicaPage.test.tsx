import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { EstructuraAcademicaPage } from '@/features/admin/pages/EstructuraAcademicaPage';
import { AuthProvider } from '@/shared/hooks/useAuth';
import { setupLocalStorage, clearLocalStorage } from '@/tests/mocks';

function renderWithProviders() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter initialEntries={['/admin/estructura']}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route path="/admin/estructura" element={<EstructuraAcademicaPage />} />
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

vi.mock('@/features/admin/services/estructura.service', () => ({
  getCarreras: vi.fn().mockResolvedValue([
    { id: '1', codigo: 'ING', nombre: 'Ingeniería', activa: true },
    { id: '2', codigo: 'LIC', nombre: 'Licenciatura', activa: false },
  ]),
  createCarrera: vi.fn(),
  updateCarrera: vi.fn(),
  toggleCarreraEstado: vi.fn(),
  getCohortes: vi.fn().mockResolvedValue([]),
  createCohorte: vi.fn(),
  updateCohorte: vi.fn(),
  toggleCohorteEstado: vi.fn(),
  getMaterias: vi.fn().mockResolvedValue([
    { id: '1', nombre: 'Matemáticas', codigo: 'MAT101', activa: true },
  ]),
  createMateria: vi.fn(),
  updateMateria: vi.fn(),
  toggleMateriaEstado: vi.fn(),
}));

describe('EstructuraAcademicaPage', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('renderiza tabs de carreras, cohortes y materias', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['estructura:gestionar'],
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Estructura Académica')).toBeInTheDocument();
    });

    expect(screen.getByText('Carreras')).toBeInTheDocument();
    expect(screen.getByText('Cohortes')).toBeInTheDocument();
    expect(screen.getByText('Materias')).toBeInTheDocument();
  });

  it('muestra lista de carreras en tab Carreras', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['estructura:gestionar'],
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Ingeniería')).toBeInTheDocument();
    });

    expect(screen.getByText('Licenciatura')).toBeInTheDocument();
  });

  it('abre formulario de nueva carrera', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['estructura:gestionar'],
    });

    const user = userEvent.setup();
    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Nueva Carrera')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Nueva Carrera'));

    expect(screen.getByLabelText('Código')).toBeInTheDocument();
    expect(screen.getByLabelText('Nombre')).toBeInTheDocument();
  });

  it('cambia a tab Materias y muestra lista', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['estructura:gestionar'],
    });

    const user = userEvent.setup();
    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Carreras')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Materias'));

    await waitFor(() => {
      expect(screen.getByText('Matemáticas')).toBeInTheDocument();
    });
  });
});
