import api from '@/shared/services/api';

import type { AccionPorDia, EstadoComunicacion, InteraccionDocente, LogEntry, AuditoriaFilter, AuditoriaPanelResponse, AuditoriaPanelUltimasResponse, LogAuditoriaResponse } from '@/features/admin/types/auditoria.types';

export async function getAccionesPorDia(filter?: AuditoriaFilter): Promise<AccionPorDia[]> {
  const { data } = await api.get<AuditoriaPanelResponse<AccionPorDia>>('/auditoria/panel/acciones-por-dia', { params: filter });
  return data.items;
}

export async function getEstadoComunicaciones(filter?: AuditoriaFilter): Promise<EstadoComunicacion[]> {
  const { data } = await api.get<AuditoriaPanelResponse<EstadoComunicacion>>('/auditoria/panel/estado-comunicaciones', { params: filter });
  return data.items;
}

export async function getInteraccionesDocente(filter?: AuditoriaFilter): Promise<InteraccionDocente[]> {
  const { data } = await api.get<AuditoriaPanelResponse<InteraccionDocente>>('/auditoria/panel/interacciones', { params: filter });
  return data.items;
}

export async function getUltimasAcciones(limit?: number): Promise<LogEntry[]> {
  const { data } = await api.get<AuditoriaPanelUltimasResponse<LogEntry>>('/auditoria/panel/ultimas-acciones', { params: { limit } });
  return data.items;
}

export async function getLogAuditoria(filter?: AuditoriaFilter): Promise<LogAuditoriaResponse> {
  const params: Record<string, string | number | undefined> = {
    accion: filter?.accion,
    usuario_id: filter?.usuario_id,
    fecha_desde: filter?.fecha_desde,
    fecha_hasta: filter?.fecha_hasta,
    offset: filter?.offset ?? 0,
    limit: filter?.limit ?? 50,
  };
  const { data } = await api.get<LogAuditoriaResponse>('/auditoria/log', { params });
  return data;
}
