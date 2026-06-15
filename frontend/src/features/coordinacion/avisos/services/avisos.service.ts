import api from '@/shared/services/api';

import type {
  Aviso,
  AvisoFormData,
  AcuseRecibo,
  AvisosFilters,
} from '@/features/coordinacion/avisos/types/avisos.types';

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  total_pages: number;
}

export async function getAvisos(
  page: number,
  filters?: AvisosFilters
): Promise<PaginatedResponse<Aviso>> {
  const offset = (page - 1) * 20;
  const params: Record<string, unknown> = { offset, limit: 20, admin: true };
  if (filters?.activo !== undefined) params.activo = filters.activo;
  if (filters?.alcance) params.alcance = filters.alcance;
  if (filters?.busqueda) params.busqueda = filters.busqueda;
  const { data } = await api.get<{ items: Aviso[]; total: number }>('/avisos', { params });
  return {
    data: data.items,
    total: data.total,
    page,
    total_pages: Math.ceil(data.total / 20),
  };
}

export async function getAviso(id: string): Promise<Aviso> {
  const { data } = await api.get(`/avisos/${id}`);
  return data;
}

export async function crearAviso(payload: AvisoFormData): Promise<Aviso> {
  const { data } = await api.post('/avisos', payload);
  return data;
}

export async function editarAviso(id: string, payload: AvisoFormData): Promise<Aviso> {
  const { data } = await api.put(`/avisos/${id}`, payload);
  return data;
}

export async function eliminarAviso(id: string): Promise<void> {
  await api.delete(`/avisos/${id}`);
}

export async function getAcuses(avisoId: string): Promise<AcuseRecibo[]> {
  const { data } = await api.get(`/avisos/${avisoId}/acuses`);
  return data;
}
