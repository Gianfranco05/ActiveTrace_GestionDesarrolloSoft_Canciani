export interface ColoquioMetricas {
  total_alumnos: number;
  instancias_activas: number;
  reservas_activas: number;
  notas_registradas: number;
}

export interface Convocatoria {
  id: string;
  materia_id: string;
  materia_nombre: string;
  instancia: string;
  tipo: string;
  cohorte_id: string;
  cupos_por_dia: ConvocatoriaDia[];
  total_convocados: number;
  reservas_activas: number;
  cupos_libres: number;
  activa: boolean;
  created_at: string;
}

export interface ConvocatoriaDia {
  id: string;
  fecha: string;
  cupo: number;
}

export interface ConvocatoriaFormData {
  materia_id: string;
  cohorte_id: string;
  tipo: 'Parcial' | 'TP' | 'Coloquio' | 'Recuperatorio';
  instancia: string;
  cupos_por_dia: { fecha: string; cupo: number }[];
}

export interface AgendaReserva {
  id: string;
  convocatoria_id: string;
  convocatoria_nombre: string;
  materia_nombre: string;
  alumno_nombre: string;
  dia: string;
  horario: string;
  estado: string;
}

export interface AgendaReservasFilters {
  materia_id?: string;
  convocatoria_id?: string;
  dia?: string;
}

export interface RegistroAcademicoRow {
  id: string;
  alumno_nombre: string;
  materia_nombre: string;
  instancia: string;
  nota: number | null;
  fecha_registro: string;
}
