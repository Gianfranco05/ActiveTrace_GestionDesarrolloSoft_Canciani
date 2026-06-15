export interface Calificacion {
  id: string;
  alumnoId: string;
  actividadId: string;
  calificacion?: number;
  estado: string;
}

export interface ActividadDetectada {
  id: string;
  nombre: string;
  fecha: string;
  alumnosCount: number;
  seleccionada: boolean;
}

export interface PreviewResponse {
  actividades: ActividadDetectada[];
  totalAlumnos: number;
  materiaId: string;
  materiaNombre: string;
}

export interface UmbralConfig {
  materiaId: string;
  porcentaje: number;
  tieneCalificaciones: boolean;
}
