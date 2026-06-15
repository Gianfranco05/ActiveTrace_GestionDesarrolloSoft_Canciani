export interface CrearCohortePayload {
  identificador: string;
  nombre: string;
  vigencia_desde: string;
  vigencia_hasta: string;
  activo: boolean;
}

export interface Cohorte {
  id: string;
  identificador: string;
  nombre: string;
  vigencia_desde: string;
  vigencia_hasta: string;
  activo: boolean;
}

export interface SetupClonePayload {
  materia_id: string;
  carrera_id: string;
  cohorte_origen_id: string;
  cohorte_destino_id: string;
}

export interface CargarProgramaPayload {
  materia_id: string;
  titulo: string;
  archivo: File;
}

export interface FechaEvaluacion {
  id?: string;
  materia_id: string;
  tipo: string;
  instancia: number;
  fecha: string;
  titulo: string;
}

export interface FechaEvaluacionPayload {
  materia_id: string;
  tipo: string;
  instancia: number;
  fecha: string;
  titulo: string;
}

export type SetupStep = 1 | 2 | 3 | 4 | 5 | 6 | 7;
