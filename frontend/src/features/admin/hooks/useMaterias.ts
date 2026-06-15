import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { getMaterias, createMateria, updateMateria, toggleMateriaEstado } from '@/features/admin/services/estructura.service';

import type { CreateMateriaPayload } from '@/features/admin/types/estructura.types';

export function useMaterias() {
  return useQuery({
    queryKey: ['estructura', 'materias'],
    queryFn: getMaterias,
  });
}

export function useMutateMateria() {
  const queryClient = useQueryClient();

  const create = useMutation({
    mutationFn: (payload: CreateMateriaPayload) => createMateria(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['estructura', 'materias'] }),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreateMateriaPayload> }) =>
      updateMateria(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['estructura', 'materias'] }),
  });

  const toggleEstado = useMutation({
    mutationFn: (id: string) => toggleMateriaEstado(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['estructura', 'materias'] }),
  });

  return { create, update, toggleEstado };
}
