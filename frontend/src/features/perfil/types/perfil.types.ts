export interface PerfilResponse {
  id: string;
  tenant_id: string;
  nombre: string;
  apellidos: string;
  email: string;
  dni: string | null;
  cuil: string | null;
  banco: string | null;
  cbu: string | null;
  alias_cbu: string | null;
  regional: string | null;
  legajo: string | null;
  legajo_profesional: string | null;
  facturador: boolean;
  estado: string;
  created_at: string;
  updated_at: string;
}

export interface PerfilUpdateRequest {
  nombre?: string | null;
  apellidos?: string | null;
  dni?: string | null;
  banco?: string | null;
  cbu?: string | null;
  alias_cbu?: string | null;
  regional?: string | null;
  legajo_profesional?: string | null;
  facturador?: boolean | null;
}
