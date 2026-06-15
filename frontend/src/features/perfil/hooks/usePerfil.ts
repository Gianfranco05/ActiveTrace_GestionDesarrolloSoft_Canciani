import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { getPerfil, updatePerfil } from '@/features/perfil/services/perfil.service';

import type { PerfilUpdateRequest } from '../types/perfil.types';

export function usePerfil() {
  return useQuery({
    queryKey: ['perfil'],
    queryFn: getPerfil,
  });
}

export function useUpdatePerfil() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: PerfilUpdateRequest) => updatePerfil(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['perfil'] });
    },
  });
}
