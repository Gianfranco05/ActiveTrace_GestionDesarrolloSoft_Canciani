import api from '@/shared/services/api';

import type {
  MonitorGeneralRow,
  MonitorDocenteRow,
  MonitorGeneralFilters,
  MonitorDocenteFilters,
} from '@/features/coordinacion/monitores/types/monitores.types';

export async function getMonitorGeneral(
  page: number,
  filters?: MonitorGeneralFilters
): Promise<{ data: MonitorGeneralRow[]; total: number; page: number; total_pages: number }> {
  const { data } = await api.get('/analisis/monitor/general', {
    params: { page, ...filters },
  });
  // Backend returns plain array — wrap in paginated response
  const items = Array.isArray(data) ? data : (data.items ?? []);
  return { data: items, total: items.length, page, total_pages: 1 };
}

export async function getMonitorGeneralInfinito(
  _cursor?: string,
  filters?: MonitorGeneralFilters
): Promise<{ data: MonitorGeneralRow[]; next_cursor?: string }> {
  const { data } = await api.get('/analisis/monitor/general', {
    params: { ...filters },
  });
  const items = Array.isArray(data) ? data : (data.items ?? []);
  return { data: items };
}

export async function getMonitorDocente(
  page: number,
  filters?: MonitorDocenteFilters
): Promise<{ data: MonitorDocenteRow[]; total: number; page: number; total_pages: number }> {
  const params: Record<string, unknown> = { page };
  if (filters?.materia_id) params.materia_id = filters.materia_id;
  if (filters?.docente_id) params.docente_id = filters.docente_id;
  const { data } = await api.get('/analisis/monitor/seguimiento', { params });
  const items = Array.isArray(data) ? data : (data.items ?? []);
  return { data: items, total: items.length, page, total_pages: 1 };
}

export async function exportarMonitores(
  _tipo: 'general' | 'seguimiento',
  _filters?: MonitorGeneralFilters | MonitorDocenteFilters
): Promise<Blob> {
  const { data } = await api.get('/analisis/monitor/general', { responseType: 'blob' });
  return data;
}
