export interface AccionPorDia {
  dia: string;
  total_acciones: number;
}

export interface EstadoComunicacion {
  usuario_id: string;
  usuario_nombre: string | null;
  materia_id: string | null;
  materia_nombre: string | null;
  pendiente: number;
  enviando: number;
  enviado: number;
  error: number;
  cancelado: number;
}

export interface InteraccionDocente {
  usuario_id: string;
  usuario_nombre: string | null;
  materia_id: string | null;
  materia_nombre: string | null;
  accion: string;
  cantidad: number;
}

export interface LogEntry {
  id: string;
  fecha_hora: string;
  actor_nombre: string | null;
  materia_nombre: string | null;
  accion: string;
  filas_afectadas: number;
  ip: string | null;
  user_agent: string | null;
}

export interface AuditoriaFilter {
  fecha_desde?: string;
  fecha_hasta?: string;
  materia_id?: string;
  usuario_id?: string;
  accion?: string;
  offset?: number;
  limit?: number;
}

export interface AuditoriaPanelResponse<T> {
  items: T[];
}

export interface AuditoriaPanelUltimasResponse<T> {
  items: T[];
  max_registros: number;
}

export interface LogAuditoriaResponse {
  items: LogEntry[];
  total: number;
  offset: number;
  limit: number;
}
