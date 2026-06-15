import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  getAvisos,
  getAviso,
  crearAviso,
  editarAviso,
  eliminarAviso,
  getAcuses,
  type PaginatedResponse,
} from '@/features/coordinacion/avisos/services/avisos.service';

import type {
  Aviso,
  AvisoFormData,
  AcuseRecibo,
  AvisosFilters,
} from '@/features/coordinacion/avisos/types/avisos.types';

export function useAvisos(page: number, filters?: AvisosFilters) {
  return useQuery<PaginatedResponse<Aviso>>({
    queryKey: ['avisos', page, filters],
    queryFn: () => getAvisos(page, filters),
  });
}

export function useAviso(id: string) {
  return useQuery<Aviso>({
    queryKey: ['aviso', id],
    queryFn: () => getAviso(id),
    enabled: !!id,
  });
}

export function useCrearAviso() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AvisoFormData) => crearAviso(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['avisos'] });
    },
  });
}

export function useEditarAviso() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: AvisoFormData }) => editarAviso(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['avisos'] });
    },
  });
}

export function useEliminarAviso() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => eliminarAviso(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['avisos'] });
    },
  });
}

export function useAcuses(avisoId: string) {
  return useQuery<AcuseRecibo[]>({
    queryKey: ['acuses', avisoId],
    queryFn: () => getAcuses(avisoId),
    enabled: !!avisoId,
  });
}
