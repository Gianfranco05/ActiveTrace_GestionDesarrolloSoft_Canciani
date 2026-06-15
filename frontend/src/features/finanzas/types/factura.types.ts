export interface Factura {
  id: string;
  docente_id: string;
  docente_nombre: string;
  periodo: string;
  detalle: string;
  archivo_nombre: string;
  archivo_tamano: number;
  estado: 'Pendiente' | 'Abonada';
  fecha_carga: string;
  fecha_abono: string | null;
}

export interface CreateFacturaPayload {
  docente_id: string;
  periodo: string;
  detalle: string;
  archivo: File;
}

export interface FacturaFilter {
  docente_id?: string;
  estado?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  busqueda?: string;
}
