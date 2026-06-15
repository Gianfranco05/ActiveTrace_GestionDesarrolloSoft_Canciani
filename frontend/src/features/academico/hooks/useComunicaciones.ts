import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { getPreview, enviarComunicacion, getEstadoComunicaciones, cancelarComunicacion } from '@/features/academico/services/comunicaciones.service';

import type { ComunicacionPreview, EstadoComunicacion } from '@/features/academico/types/comunicaciones.types';

export function usePreview(alumnosIds: string[]) {
  return useQuery<ComunicacionPreview[]>({
    queryKey: ['comunicaciones', 'preview', alumnosIds],
    queryFn: () => getPreview(alumnosIds),
    enabled: alumnosIds.length > 0,
  });
}

export function useEnviarComunicacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { alumnosIds: string[]; materiaId: string }) =>
      enviarComunicacion(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comunicaciones'] });
    },
  });
}

export function useEstadoComunicaciones(loteId: string | null) {
  const { data, ...rest } = useQuery<EstadoComunicacion[]>({
    queryKey: ['comunicaciones', 'estado', loteId],
    queryFn: () => getEstadoComunicaciones(loteId!),
    enabled: !!loteId,
    refetchInterval: (query) => {
      if (!query.state.data) return 5000;
      const hasPending = query.state.data.some(
        (e) => e.estado === 'Pendiente' || e.estado === 'Enviando'
      );
      return hasPending ? 5000 : false;
    },
  });

  const allInFinalState = data
    ? data.every((e) => ['Enviado', 'Error', 'Cancelado'].includes(e.estado))
    : false;

  return { data, allInFinalState, ...rest };
}

export function useCancelarComunicacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (loteId: string) => cancelarComunicacion(loteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comunicaciones'] });
    },
  });
}
