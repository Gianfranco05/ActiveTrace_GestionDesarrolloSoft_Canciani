import { useQuery } from '@tanstack/react-query';

import { getHistorialLiquidaciones } from '@/features/finanzas/services/liquidacion.service';

export function useHistorialLiquidaciones(cohorte_id?: string) {
  return useQuery({
    queryKey: ['liquidaciones', 'historial', cohorte_id],
    queryFn: () => getHistorialLiquidaciones(cohorte_id),
    enabled: !!cohorte_id,
  });
}
