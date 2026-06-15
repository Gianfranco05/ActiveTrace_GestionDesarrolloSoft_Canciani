import { useQuery } from '@tanstack/react-query';

import { getNotasFinales } from '@/features/academico/services/analisis.service';

import type { NotaFinal } from '@/features/academico/types/analisis.types';

export function useNotasFinales(materiaId: string) {
  return useQuery<NotaFinal[]>({
    queryKey: ['analisis', 'notas-finales', materiaId],
    queryFn: () => getNotasFinales(materiaId),
    enabled: !!materiaId,
  });
}
