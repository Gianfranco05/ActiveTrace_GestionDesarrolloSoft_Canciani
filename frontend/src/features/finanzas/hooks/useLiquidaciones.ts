import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { getLiquidaciones, getLiquidacionKPI, cerrarLiquidacion, calcularLiquidacion } from '@/features/finanzas/services/liquidacion.service';

import type { LiquidacionFilter, CerrarLiquidacionPayload } from '@/features/finanzas/types/liquidacion.types';

export function useLiquidaciones(filter?: LiquidacionFilter) {
  return useQuery({
    queryKey: ['liquidaciones', filter],
    queryFn: () => getLiquidaciones(filter),
  });
}

export function useLiquidacionKPI(filter?: LiquidacionFilter) {
  return useQuery({
    queryKey: ['liquidaciones', 'kpi', filter],
    queryFn: () => getLiquidacionKPI(filter),
  });
}

export function useCerrarLiquidacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CerrarLiquidacionPayload) => cerrarLiquidacion(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['liquidaciones'] });
    },
  });
}

export function useCalcularLiquidacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ cohorte_id, periodo }: { cohorte_id: string; periodo: string }) =>
      calcularLiquidacion(cohorte_id, periodo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['liquidaciones'] });
    },
  });
}
