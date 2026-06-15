import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { getCohortes, createCohorte, updateCohorte, toggleCohorteEstado } from '@/features/admin/services/estructura.service';

import type { CreateCohortePayload } from '@/features/admin/types/estructura.types';

export function useCohortes(carrera_id?: string) {
  return useQuery({
    queryKey: ['estructura', 'cohortes', carrera_id],
    queryFn: () => getCohortes(carrera_id),
    enabled: !!carrera_id,
  });
}

export function useMutateCohorte() {
  const queryClient = useQueryClient();

  const create = useMutation({
    mutationFn: (payload: CreateCohortePayload) => createCohorte(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['estructura', 'cohortes'] }),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreateCohortePayload> }) =>
      updateCohorte(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['estructura', 'cohortes'] }),
  });

  const toggleEstado = useMutation({
    mutationFn: (id: string) => toggleCohorteEstado(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['estructura', 'cohortes'] }),
  });

  return { create, update, toggleEstado };
}
