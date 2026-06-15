import api from '@/shared/services/api';

import type { PerfilResponse, PerfilUpdateRequest } from '../types/perfil.types';

export async function getPerfil(): Promise<PerfilResponse> {
  const { data } = await api.get('/perfil');
  return data;
}

export async function updatePerfil(body: PerfilUpdateRequest): Promise<PerfilResponse> {
  const { data } = await api.put('/perfil', body);
  return data;
}
