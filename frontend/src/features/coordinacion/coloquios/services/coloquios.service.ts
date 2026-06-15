import api from '@/shared/services/api';

import type {
  ColoquioMetricas,
  Convocatoria,
  ConvocatoriaFormData,
  AgendaReserva,
  AgendaReservasFilters,
  RegistroAcademicoRow,
} from '@/features/coordinacion/coloquios/types/coloquios.types';

export async function getMetricas(): Promise<ColoquioMetricas> {
  const { data } = await api.get('/coloquios/metricas');
  return data;
}

export async function getConvocatorias(): Promise<Convocatoria[]> {
  const { data } = await api.get<{ items: Convocatoria[] }>('/coloquios/');
  return data.items ?? data as any;
}

export async function crearConvocatoria(payload: ConvocatoriaFormData): Promise<Convocatoria> {
  const { data } = await api.post('/coloquios/', payload);
  return data;
}

export async function importarAlumnos(convocatoriaId: string, archivo: File): Promise<void> {
  const formData = new FormData();
  formData.append('archivo', archivo);
  await api.post(`/coloquios/${convocatoriaId}/importar`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export async function getReservas(filters?: AgendaReservasFilters): Promise<AgendaReserva[]> {
  const params: Record<string, string> = {};
  if (filters?.materia_id) params.materia_id = filters.materia_id;
  if (filters?.convocatoria_id) params.evaluacion_id = filters.convocatoria_id;
  if (filters?.dia) {
    params.fecha_desde = filters.dia;
    params.fecha_hasta = filters.dia;
  }
  const { data } = await api.get<{ items: AgendaReserva[] }>('/coloquios/admin/agenda', { params });
  return data.items ?? [];
}

export async function getRegistroAcademico(): Promise<RegistroAcademicoRow[]> {
  const { data } = await api.get('/coloquios/registro');
  return data;
}
