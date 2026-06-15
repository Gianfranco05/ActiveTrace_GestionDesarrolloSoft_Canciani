import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  crearCohorte,
  clonarEquipoSetup,
  cargarPrograma,
  getFechasEvaluaciones,
  crearFechaEvaluacion,
  eliminarFechaEvaluacion,
  getCohortes,
  getCohorte,
} from '@/features/coordinacion/setup/services/setup.service';

import type {
  CrearCohortePayload,
  Cohorte,
  SetupClonePayload,
  FechaEvaluacion,
  FechaEvaluacionPayload,
} from '@/features/coordinacion/setup/types/setup.types';

export function useCohortes() {
  return useQuery<Cohorte[]>({
    queryKey: ['cohortes'],
    queryFn: getCohortes,
  });
}

export function useCohorte(id: string) {
  return useQuery<Cohorte>({
    queryKey: ['cohorte', id],
    queryFn: () => getCohorte(id),
    enabled: !!id,
  });
}

export function useCrearCohorte() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CrearCohortePayload) => crearCohorte(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cohortes'] });
    },
  });
}

export function useClonarEquipoSetup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SetupClonePayload) => clonarEquipoSetup(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mis-equipos'] });
    },
  });
}

export function useCargarPrograma() {
  return useMutation({
    mutationFn: ({ materiaId, titulo, archivo }: { materiaId: string; titulo: string; archivo: File }) =>
      cargarPrograma(materiaId, titulo, archivo),
  });
}

export function useFechasEvaluaciones(cohorteId: string) {
  return useQuery<FechaEvaluacion[]>({
    queryKey: ['fechas-evaluaciones', cohorteId],
    queryFn: () => getFechasEvaluaciones(cohorteId),
    enabled: !!cohorteId,
  });
}

export function useCrearFechaEvaluacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: FechaEvaluacionPayload) => crearFechaEvaluacion(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fechas-evaluaciones'] });
    },
  });
}

export function useEliminarFechaEvaluacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => eliminarFechaEvaluacion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fechas-evaluaciones'] });
    },
  });
}
