import { useQuery } from '@tanstack/react-query';

import { getReportesRapidos } from '@/features/academico/services/analisis.service';

import type { MetricaReporte } from '@/features/academico/types/analisis.types';

export function useReportes(materiaId: string) {
  return useQuery<MetricaReporte>({
    queryKey: ['analisis', 'reportes', materiaId],
    queryFn: () => getReportesRapidos(materiaId),
    enabled: !!materiaId,
  });
}
