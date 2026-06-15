import { useQuery } from '@tanstack/react-query';

import { getMonitores } from '@/features/academico/services/analisis.service';

import type { EntradaMonitor } from '@/features/academico/types/analisis.types';

export function useMonitores(filtros: Record<string, string | number | undefined>) {
  return useQuery<EntradaMonitor[]>({
    queryKey: ['analisis', 'monitores', filtros],
    queryFn: () => getMonitores(filtros),
    enabled: Object.keys(filtros).length > 0,
  });
}
