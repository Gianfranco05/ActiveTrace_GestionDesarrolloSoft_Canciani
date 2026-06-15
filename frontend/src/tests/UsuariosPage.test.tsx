import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { UsuariosPage } from '@/features/admin/pages/UsuariosPage';
import { AuthProvider } from '@/shared/hooks/useAuth';
import { setupLocalStorage, clearLocalStorage } from '@/tests/mocks';

function renderWithProviders() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <MemoryRouter initialEntries={['/admin/usuarios']}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route path="/admin/usuarios" element={<UsuariosPage />} />
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

vi.mock('@/features/admin/services/usuario.service', () => ({
  getUsuarios: vi.fn(),
  createUsuario: vi.fn(),
  updateUsuario: vi.fn(),
  toggleUsuarioEstado: vi.fn(),
}));

describe('UsuariosPage', () => {
  beforeEach(() => {
    clearLocalStorage();
    vi.clearAllMocks();
  });

  it('renderiza listado de usuarios con filtros', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['usuarios:gestionar'],
    });

    const mockedService = await import('@/features/admin/services/usuario.service');
    vi.mocked(mockedService.getUsuarios).mockResolvedValue([
      { id: '1', nombre: 'Juan Pérez', email: 'juan@test.com', roles: ['profesor'], activo: true, ultimo_acceso: '2026-06-01T10:00:00Z', datos_bancarios: null },
      { id: '2', nombre: 'María López', email: 'maria@test.com', roles: ['admin'], activo: false, ultimo_acceso: null, datos_bancarios: null },
    ]);

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Usuarios')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Juan Pérez')).toBeInTheDocument();
    });
    expect(screen.getByText('María López')).toBeInTheDocument();
  });

  it('renderiza filtros de rol, estado y búsqueda', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['usuarios:gestionar'],
    });

    const mockedService = await import('@/features/admin/services/usuario.service');
    vi.mocked(mockedService.getUsuarios).mockResolvedValue([]);

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByLabelText('Rol')).toBeInTheDocument();
    });

    expect(screen.getByLabelText('Estado')).toBeInTheDocument();
    expect(screen.getByLabelText('Buscar')).toBeInTheDocument();
  });

  it('abre formulario de nuevo usuario', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['usuarios:gestionar'],
    });

    const mockedService = await import('@/features/admin/services/usuario.service');
    vi.mocked(mockedService.getUsuarios).mockResolvedValue([]);

    const user = userEvent.setup();
    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Nuevo Usuario')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Nuevo Usuario'));

    expect(screen.getByLabelText('Nombre')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });

  it('muestra botones de activar/desactivar', async () => {
    setupLocalStorage();
    const mockedAuthService = await import('@/features/auth/services/auth.service');
    vi.mocked(mockedAuthService.me).mockResolvedValue({
      id: '1', email: 'test@test.com', name: 'Admin', roles: ['admin'], permissions: ['usuarios:gestionar'],
    });

    const mockedService = await import('@/features/admin/services/usuario.service');
    vi.mocked(mockedService.getUsuarios).mockResolvedValue([
      { id: '1', nombre: 'Juan Pérez', email: 'juan@test.com', roles: ['profesor'], activo: true, ultimo_acceso: '2026-06-01T10:00:00Z', datos_bancarios: null },
    ]);

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('Desactivar')).toBeInTheDocument();
    });
  });
});
