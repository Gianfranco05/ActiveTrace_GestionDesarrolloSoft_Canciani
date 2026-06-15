export type EncuentroEstado = 'programado' | 'realizado' | 'cancelado' | 'pendiente';

export interface Encuentro {
  id: string;
  materia_id: string;
  materia_nombre: string;
  docente_id: string;
  docente_nombre: string;
  fecha: string;
  horario: string;
  titulo: string;
  enlace: string | null;
  grabacion: string | null;
  estado: EncuentroEstado;
  comentario: string | null;
  es_recurrente: boolean;
  created_at: string;
}

export interface EncuentroRecurrenteForm {
  materia_id: string;
  dia_semana: number;
  horario: string;
  fecha_inicio: string;
  semanas: number;
  titulo: string;
  enlace: string;
}

export interface EncuentroUnicoForm {
  materia_id: string;
  fecha: string;
  horario: string;
  titulo: string;
  enlace: string;
}

export interface EncuentroEditForm {
  estado?: EncuentroEstado;
  enlace?: string;
  grabacion?: string;
  comentario?: string;
}

export interface EncuentrosFilters {
  materia_id?: string;
  q?: string;
  estado?: EncuentroEstado;
  fecha_desde?: string;
  fecha_hasta?: string;
}

export interface ContenidoAulaVirtual {
  contenido: string;
}
