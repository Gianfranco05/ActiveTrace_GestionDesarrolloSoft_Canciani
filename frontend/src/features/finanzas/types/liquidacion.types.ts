export interface Liquidacion {
  id: string;
  docente_id: string;
  docente_nombre: string;
  rol: string;
  comisiones: number;
  monto_base: number;
  monto_plus: number;
  total: number;
  es_nexo: boolean;
  excluido_por_factura: boolean;
  cohorte_id: string;
  periodo: string;
  estado: 'Abierta' | 'Cerrada';
  created_at: string;
}

export interface LiquidacionKPI {
  total_general: number;
  total_sin_factura: number;
  total_nexo: number;
  total_facturantes: number;
  total_docentes: number;
}

export interface CerrarLiquidacionPayload {
  cohorte_id: string;
  periodo: string;
}

export interface LiquidacionFilter {
  cohorte_id?: string;
  mes?: string;
}

export interface HistorialLiquidacion {
  id: string;
  periodo: string;
  cohorte_nombre: string;
  total_liquidado: number;
  cantidad_docentes: number;
  fecha_cierre: string;
}
