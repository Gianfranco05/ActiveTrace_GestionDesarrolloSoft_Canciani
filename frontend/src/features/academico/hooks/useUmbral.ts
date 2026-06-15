import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { getUmbral, setUmbral } from '@/features/academico/services/calificaciones.service';

import type { UmbralConfig } from '@/features/academico/types/calificaciones.types';

export function useUmbral(materiaId: string) {
  return useQuery<UmbralConfig>({
    queryKey: ['calificaciones', 'umbral', materiaId],
    queryFn: () => getUmbral(materiaId),
    enabled: !!materiaId,
  });
}

export function useSetUmbral() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ materiaId, porcentaje }: { materiaId: string; porcentaje: number }) =>
      setUmbral(materiaId, porcentaje),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['calificaciones', 'umbral', variables.materiaId] });
    },
  });
}
