export interface AsignacionResponse {
  id: string;
  tenant_id: string;
  usuario_id: string;
  rol_id: string;
  rol_nombre: string;
  materia_id: string | null;
  carrera_id: string | null;
  cohorte_id: string | null;
  comisiones: string | null;
  responsable_id: string | null;
  vig_desde: string;
  vig_hasta: string | null;
  estado_vigencia: string;
}

export interface EquipoDetailResponse {
  materia_id: string;
  carrera_id: string;
  cohorte_id: string;
  asignaciones: AsignacionResponse[];
}

export interface MisMateria {
  id: string;
  nombre: string;
  comision: string | null;
}

export interface UsuarioSearchResult {
  id: string;
  nombre: string;
  apellidos: string;
  legajo: string | null;
}

export interface AsignacionMasivaPayload {
  materia_id: string;
  carrera_id: string;
  cohorte_id: string;
  rol_id: string;
  usuario_ids: string[];
  vig_desde: string;
  vig_hasta: string | null;
  comisiones: string | null;
}

export interface ClonarEquipoPayload {
  origen_materia_id: string;
  origen_carrera_id: string;
  origen_cohorte_id: string;
  destino_materia_id: string;
  destino_carrera_id: string;
  destino_cohorte_id: string;
  nueva_vig_desde: string;
  nueva_vig_hasta: string | null;
}

export interface VigenciaPayload {
  materia_id: string;
  carrera_id: string;
  cohorte_id: string;
  vig_desde: string;
  vig_hasta: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface EquiposFilters {
  estado?: string;
  materia_id?: string;
  rol_id?: string;
  carrera_id?: string;
  cohorte_id?: string;
}

export interface AsignacionesFilters {
  usuario_id?: string;
  rol_id?: string;
}
