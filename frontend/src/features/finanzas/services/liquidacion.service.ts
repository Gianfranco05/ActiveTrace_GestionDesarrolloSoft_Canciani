import api from '@/shared/services/api';

import type { Liquidacion, LiquidacionKPI, CerrarLiquidacionPayload, LiquidacionFilter, HistorialLiquidacion } from '@/features/finanzas/types/liquidacion.types';

function buildQueryParams(filter?: LiquidacionFilter): Record<string, string> {
  const params: Record<string, string> = {};
  if (filter?.cohorte_id) params.cohorte_id = filter.cohorte_id;
  if (filter?.mes) params.periodo = `${new Date().getFullYear()}-${filter.mes}`;
  return params;
}

export async function getLiquidaciones(filter?: LiquidacionFilter): Promise<Liquidacion[]> {
  const { data } = await api.get<Liquidacion[]>('/liquidaciones', { params: buildQueryParams(filter) });
  return data;
}

export async function getLiquidacionKPI(filter?: LiquidacionFilter): Promise<LiquidacionKPI> {
  const { data } = await api.get<LiquidacionKPI>('/liquidaciones/kpi', { params: buildQueryParams(filter) });
  return data;
}

export async function cerrarLiquidacion(payload: CerrarLiquidacionPayload): Promise<void> {
  await api.post(`/liquidaciones/${payload.cohorte_id}/${payload.periodo}/cerrar`);
}

export async function getHistorialLiquidaciones(cohorte_id?: string): Promise<HistorialLiquidacion[]> {
  const params: Record<string, string> = {};
  if (cohorte_id) params.cohorte_id = cohorte_id;
  const { data } = await api.get<HistorialLiquidacion[]>('/liquidaciones/historial', { params });
  return data;
}

export async function calcularLiquidacion(cohorte_id: string, periodo: string): Promise<{ liquidaciones: Liquidacion[]; kpis: LiquidacionKPI; docentes_excluidos: Record<string, unknown>[] }> {
  const { data } = await api.post('/liquidaciones/calcular', { cohorte_id, periodo });
  return data;
}
