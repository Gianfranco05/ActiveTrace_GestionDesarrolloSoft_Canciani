import { useQuery } from '@tanstack/react-query';

import { getAtrasados } from '@/features/academico/services/analisis.service';

import type { AlumnoAtrasado } from '@/features/academico/types/analisis.types';

export function useAtrasados(
  materiaId: string,
  filtros?: { minFaltantes?: number; maxPorcentaje?: number }
) {
  return useQuery<AlumnoAtrasado[]>({
    queryKey: ['analisis', 'atrasados', materiaId, filtros],
    queryFn: () => getAtrasados(materiaId, filtros),
    enabled: !!materiaId,
  });
}
