import type { User } from '@/shared/types/auth';

export const mockUser: User = {
  id: '550e8400-e29b-41d4-a716-446655440000',
  email: 'admin@test.com',
  name: 'Admin Usuario',
  roles: ['admin'],
  permissions: [
    'calificaciones:ver',
    'calificaciones:importar',
    'atrasados:ver',
    'comunicacion:enviar',
    'liquidaciones:ver',
    'liquidaciones:cerrar',
    'liquidaciones:configurar-salarios',
    'facturas:gestionar',
    'estructura:gestionar',
    'usuarios:gestionar',
    'auditoria:ver',
  ],
};

export const mockAccessToken = 'mock-access-token';
export const mockRefreshToken = 'mock-refresh-token';

export function setupLocalStorage() {
  localStorage.setItem('access_token', mockAccessToken);
  localStorage.setItem('refresh_token', mockRefreshToken);
}

export function clearLocalStorage() {
  localStorage.clear();
}
