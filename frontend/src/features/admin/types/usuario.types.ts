export interface Usuario {
  id: string;
  nombre: string;
  email: string;
  roles: string[];
  activo: boolean;
  ultimo_acceso: string | null;
  datos_bancarios?: DatosBancarios | null;
}

export interface DatosBancarios {
  cbu: string;
  banco: string;
  titular: string;
}

export interface CreateUsuarioPayload {
  nombre: string;
  email: string;
  password?: string;
  roles: string[];
  datos_bancarios?: {
    cbu: string;
    banco: string;
    titular: string;
  } | null;
}

export interface UsuarioFilter {
  rol?: string;
  activo?: boolean;
  busqueda?: string;
}
