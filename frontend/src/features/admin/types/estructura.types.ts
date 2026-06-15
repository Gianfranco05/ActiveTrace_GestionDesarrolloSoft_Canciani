export interface Carrera {
  id: string;
  codigo: string;
  nombre: string;
  activa: boolean;
}

export interface Cohorte {
  id: string;
  carrera_id: string;
  nombre: string;
  anio: number;
  vig_desde: string;
  vig_hasta: string | null;
  activa: boolean;
}

export interface Materia {
  id: string;
  nombre: string;
  codigo: string;
  activa: boolean;
  grupo_plus?: string | null;
}

export interface CreateCarreraPayload {
  codigo: string;
  nombre: string;
}

export interface CreateCohortePayload {
  carrera_id: string;
  nombre: string;
  anio: number;
  vig_desde: string;
  vig_hasta?: string | null;
}

export interface CreateMateriaPayload {
  nombre: string;
  codigo: string;
  grupo_plus?: string | null;
  carrera_ids?: string[];
}
