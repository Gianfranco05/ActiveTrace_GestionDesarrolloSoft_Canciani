import api from '@/shared/services/api';

import type { Usuario, CreateUsuarioPayload, UsuarioFilter } from '@/features/admin/types/usuario.types';

export async function getUsuarios(filter?: UsuarioFilter): Promise<Usuario[]> {
  const { data } = await api.get<{ items: Usuario[]; total: number }>('/v1/admin/usuarios', { params: filter });
  return data.items;
}

function toBackendPayload(payload: CreateUsuarioPayload): Record<string, unknown> {
  const body: Record<string, unknown> = {
    nombre: payload.nombre,
    email: payload.email,
    cbu: payload.datos_bancarios?.cbu || undefined,
    banco: payload.datos_bancarios?.banco || undefined,
    roles: payload.roles,
  };
  if (payload.password) {
    body.password = payload.password;
  }
  return body;
}

export async function createUsuario(payload: CreateUsuarioPayload): Promise<Usuario> {
  const { data } = await api.post<Usuario>('/v1/admin/usuarios', toBackendPayload(payload));
  return data;
}

export async function updateUsuario(id: string, payload: Partial<CreateUsuarioPayload>): Promise<Usuario> {
  const body = toBackendPayload(payload as CreateUsuarioPayload);
  const { data } = await api.put<Usuario>(`/v1/admin/usuarios/${id}`, body);
  return data;
}

export async function toggleUsuarioEstado(id: string): Promise<Usuario> {
  const { data } = await api.patch<Usuario>(`/v1/admin/usuarios/${id}/estado`);
  return data;
}
