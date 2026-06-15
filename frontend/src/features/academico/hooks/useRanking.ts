import { useQuery } from '@tanstack/react-query';

import { getRanking } from '@/features/academico/services/analisis.service';

import type { RankingItem } from '@/features/academico/types/analisis.types';

export function useRanking(materiaId: string) {
  return useQuery<RankingItem[]>({
    queryKey: ['analisis', 'ranking', materiaId],
    queryFn: () => getRanking(materiaId),
    enabled: !!materiaId,
  });
}
