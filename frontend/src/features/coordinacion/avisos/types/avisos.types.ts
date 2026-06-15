export type AvisoAlcance = 'Global' | 'PorMateria' | 'PorCohorte' | 'PorRol';
export type AvisoSeveridad = 'Info' | 'Advertencia' | 'Critico';

export interface Aviso {
  id: string;
  titulo: string;
  cuerpo: string;
  alcance: AvisoAlcance;
  rol_destino: string | null;
  severidad: AvisoSeveridad;
  inicio_en: string | null;
  fin_en: string | null;
  orden: number;
  activo: boolean;
  requiere_ack: boolean;
  materia_id?: string | null;
  cohorte_id?: string | null;
  created_at: string;
  updated_at: string;
  total_acuses?: number;
  acuses_confirmados?: number;
}

export interface AvisoFormData {
  titulo: string;
  cuerpo: string;
  alcance: AvisoAlcance;
  rol_destino: string | null;
  severidad: AvisoSeveridad;
  inicio_en: string;
  fin_en: string;
  orden: number;
  activo: boolean;
  requiere_ack: boolean;
  materia_id?: string;
  cohorte_id?: string;
}

export interface AcuseRecibo {
  id: string;
  aviso_id: string;
  usuario_id: string;
  usuario_nombre: string;
  confirmado: boolean;
  confirmado_at: string | null;
}

export interface AvisosFilters {
  activo?: boolean;
  alcance?: AvisoAlcance;
  materia_id?: string;
  cohorte_id?: string;
  busqueda?: string;
}
