// Matching backend schemas in app/schemas/analisis.py

export interface AlumnoAtrasado {
  entrada_padron_id: string;
  nombre: string;
  apellidos: string;
  email: string | null;
  comision: string | null;
  motivo: string;
  actividades_faltantes: string[];
  actividades_reprobadas: string[];
}

export interface RankingItem {
  posicion: number;
  entrada_padron_id: string;
  nombre: string;
  apellidos: string;
  aprobadas: number;
  total_actividades: number;
  porcentaje: number;
}

export interface NotaFinal {
  entrada_padron_id: string;
  nombre: string;
  apellidos: string;
  nota_promedio: number | null;
  actividades_aprobadas: number;
  total_actividades: number;
  estado: string;
}

export interface MetricaReporte {
  materia_id: string;
  materia_nombre: string;
  cohorte_id: string;
  cohorte_nombre: string;
  total_alumnos: number;
  alumnos_con_nota: number;
  alumnos_aprobados: number;
  alumnos_atrasados: number;
  pct_aprobados: number;
  pct_atrasados: number;
  actividades_count: number;
  ultima_importacion: string | null;
}

export interface EntradaMonitor {
  alumno_id?: string;
  alumno_nombre?: string;
  actividad?: string;
  estado?: string;
  fecha?: string;
}
