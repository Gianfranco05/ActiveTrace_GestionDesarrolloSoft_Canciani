import api from '@/shared/services/api';

import type {
  AsignacionResponse,
  EquipoDetailResponse,
  EquiposFilters,
  AsignacionesFilters,
  AsignacionMasivaPayload,
  ClonarEquipoPayload,
  VigenciaPayload,
  UsuarioSearchResult,
  MisMateria,
  PaginatedResponse,
} from '@/features/coordinacion/equipos/types/equipos.types';

export type { PaginatedResponse } from '@/features/coordinacion/equipos/types/equipos.types';

const PAGE_SIZE = 20;

export async function getMisEquipos(filters?: EquiposFilters): Promise<PaginatedResponse<AsignacionResponse>> {
  const { data } = await api.get('/equipos/mis-equipos', { params: filters });
  return data;
}

export async function getAsignaciones(
  page: number,
  filters?: AsignacionesFilters
): Promise<PaginatedResponse<AsignacionResponse>> {
  const { data } = await api.get('/v1/asignaciones', {
    params: { offset: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE, ...filters },
  });
  return data;
}

export async function asignacionMasiva(
  payload: AsignacionMasivaPayload
): Promise<PaginatedResponse<AsignacionResponse>> {
  const { data } = await api.post('/equipos/masiva', payload);
  return data;
}

export async function clonarEquipo(payload: ClonarEquipoPayload): Promise<EquipoDetailResponse> {
  const { data } = await api.post('/equipos/clonar', payload);
  return data;
}

export async function modificarVigencia(payload: VigenciaPayload): Promise<void> {
  await api.patch(
    '/equipos/vigencia',
    { vig_desde: payload.vig_desde, vig_hasta: payload.vig_hasta },
    {
      params: {
        materia_id: payload.materia_id,
        carrera_id: payload.carrera_id,
        cohorte_id: payload.cohorte_id,
      },
    }
  );
}

export async function exportarEquipo(
  materia_id: string,
  carrera_id: string,
  cohorte_id: string
): Promise<Blob> {
  const { data } = await api.get('/equipos/export', {
    params: { materia_id, carrera_id, cohorte_id },
    responseType: 'blob',
  });
  return data;
}

export async function searchUsuarios(q: string): Promise<PaginatedResponse<UsuarioSearchResult>> {
  const { data } = await api.get('/equipos/usuarios/search', { params: { q } });
  return data;
}

export async function getMisMaterias(): Promise<MisMateria[]> {
  const { data } = await api.get('/equipos/mis-materias');
  return data;
}

export async function updateAsignacion(id: string, payload: Record<string, unknown>): Promise<AsignacionResponse> {
  const { data } = await api.put(`/v1/asignaciones/${id}`, payload);
  return data;
}
