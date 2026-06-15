export type TareaEstado = 'Pendiente' | 'En progreso' | 'Resuelta' | 'Cancelada';

export interface Tarea {
  id: string;
  titulo: string;
  descripcion: string;
  materia_id: string;
  materia_nombre: string;
  docente_asignado_id: string;
  docente_asignado_nombre: string;
  asignador_id: string;
  asignador_nombre: string;
  estado: TareaEstado;
  criterio_cierre: string;
  created_at: string;
  updated_at: string;
}

export interface TareaFormData {
  titulo: string;
  descripcion: string;
  materia_id: string;
  docente_asignado_id: string;
  criterio_cierre: string;
}

export interface TareaComentario {
  id: string;
  tarea_id: string;
  autor_id: string;
  autor_nombre: string;
  contenido: string;
  created_at: string;
}

export interface TareaHistorial {
  id: string;
  tarea_id: string;
  estado_anterior: TareaEstado;
  estado_nuevo: TareaEstado;
  usuario_id: string;
  usuario_nombre: string;
  created_at: string;
}

export interface TareasFilters {
  asignado_a?: string;
  materia_id?: string;
  estado?: TareaEstado;
  q?: string;
}
