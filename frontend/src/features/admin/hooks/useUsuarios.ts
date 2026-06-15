import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { getUsuarios, createUsuario, updateUsuario, toggleUsuarioEstado } from '@/features/admin/services/usuario.service';

import type { CreateUsuarioPayload, UsuarioFilter } from '@/features/admin/types/usuario.types';

export function useUsuarios(filter?: UsuarioFilter) {
  return useQuery({
    queryKey: ['usuarios', filter],
    queryFn: () => getUsuarios(filter),
  });
}

export function useMutateUsuario() {
  const queryClient = useQueryClient();

  const create = useMutation({
    mutationFn: (payload: CreateUsuarioPayload) => createUsuario(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['usuarios'] }),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreateUsuarioPayload> }) =>
      updateUsuario(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['usuarios'] }),
  });

  const toggleEstado = useMutation({
    mutationFn: (id: string) => toggleUsuarioEstado(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['usuarios'] }),
  });

  return { create, update, toggleEstado };
}
