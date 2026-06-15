export interface MonitorGeneralRow {
  id: string;
  alumno_nombre: string;
  materia_nombre: string;
  comision: string;
  regional: string;
  estado: string;
  criterio: string;
  actividades_cumplidas: number;
  actividades_totales: number;
}

export interface MonitorDocenteRow {
  id: string;
  alumno_nombre: string;
  docente_nombre: string;
  materia_nombre: string;
  comision: string;
  regional: string;
  actividades_cumplidas: number;
  correo: string;
}

export interface MonitorGeneralFilters {
  materia_id?: string;
  regional?: string;
  comision?: string;
  busqueda?: string;
  estado?: string;
  criterio?: string;
}

export interface MonitorDocenteFilters extends MonitorGeneralFilters {
  docente_id?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  minimo_actividades?: number;
}
