import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { getCarreras, createCarrera, updateCarrera, toggleCarreraEstado } from '@/features/admin/services/estructura.service';

import type { CreateCarreraPayload } from '@/features/admin/types/estructura.types';

export function useCarreras() {
  return useQuery({
    queryKey: ['estructura', 'carreras'],
    queryFn: getCarreras,
  });
}

export function useMutateCarrera() {
  const queryClient = useQueryClient();

  const create = useMutation({
    mutationFn: (payload: CreateCarreraPayload) => createCarrera(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['estructura', 'carreras'] }),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreateCarreraPayload> }) =>
      updateCarrera(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['estructura', 'carreras'] }),
  });

  const toggleEstado = useMutation({
    mutationFn: (id: string) => toggleCarreraEstado(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['estructura', 'carreras'] }),
  });

  return { create, update, toggleEstado };
}
