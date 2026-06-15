import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  getEncuentros,
  crearEncuentroRecurrente,
  crearEncuentroUnico,
  editarEncuentro,
  getContenidoAula,
  type PaginatedResponse,
} from '@/features/coordinacion/encuentros/services/encuentros.service';

import type {
  Encuentro,
  EncuentroRecurrenteForm,
  EncuentroUnicoForm,
  EncuentroEditForm,
  EncuentrosFilters,
} from '@/features/coordinacion/encuentros/types/encuentros.types';

export function useEncuentros(page: number, filters?: EncuentrosFilters) {
  return useQuery<PaginatedResponse<Encuentro>>({
    queryKey: ['encuentros', page, filters],
    queryFn: () => getEncuentros(page, filters),
  });
}

export function useCrearEncuentroRecurrente() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: EncuentroRecurrenteForm) => crearEncuentroRecurrente(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['encuentros'] });
    },
  });
}

export function useCrearEncuentroUnico() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: EncuentroUnicoForm) => crearEncuentroUnico(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['encuentros'] });
    },
  });
}

export function useEditarEncuentro() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: EncuentroEditForm }) => editarEncuentro(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['encuentros'] });
    },
  });
}

export function useContenidoAula(materiaId: string) {
  return useQuery({
    queryKey: ['contenido-aula', materiaId],
    queryFn: () => getContenidoAula(materiaId),
    enabled: !!materiaId,
  });
}
