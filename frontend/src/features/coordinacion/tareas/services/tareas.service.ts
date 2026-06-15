import api from '@/shared/services/api';

import type {
  Tarea,
  TareaFormData,
  TareaEstado,
  TareaComentario,
  TareaHistorial,
  TareasFilters,
} from '@/features/coordinacion/tareas/types/tareas.types';

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  total_pages: number;
}

export async function getTareas(
  page: number,
  filters?: TareasFilters
): Promise<PaginatedResponse<Tarea>> {
  const offset = (page - 1) * 20;
  const params: Record<string, unknown> = { offset, limit: 20 };
  if (filters?.estado) params.estado = filters.estado;
  if (filters?.materia_id) params.materia_id = filters.materia_id;
  if (filters?.asignado_a) params.asignado_a = filters.asignado_a;
  if (filters?.q) params.q = filters.q;
  const { data } = await api.get<{ items: Tarea[]; total: number }>('/tareas', { params });
  return {
    data: data.items,
    total: data.total,
    page,
    total_pages: Math.ceil(data.total / 20),
  };
}

export async function getTarea(id: string): Promise<Tarea> {
  const { data } = await api.get(`/tareas/${id}`);
  return data;
}

export async function crearTarea(payload: TareaFormData): Promise<Tarea> {
  const { data } = await api.post('/tareas', payload);
  return data;
}

export async function cambiarEstadoTarea(id: string, estado: TareaEstado): Promise<Tarea> {
  const { data } = await api.patch(`/tareas/${id}`, { estado });
  return data;
}

export async function getComentarios(tareaId: string): Promise<TareaComentario[]> {
  const { data } = await api.get(`/tareas/${tareaId}/comentarios`);
  return data;
}

export async function agregarComentario(tareaId: string, contenido: string): Promise<TareaComentario> {
  const { data } = await api.post(`/tareas/${tareaId}/comentarios`, { contenido });
  return data;
}

export async function getHistorial(tareaId: string): Promise<TareaHistorial[]> {
  const { data } = await api.get(`/tareas/${tareaId}/historial`);
  return data;
}
