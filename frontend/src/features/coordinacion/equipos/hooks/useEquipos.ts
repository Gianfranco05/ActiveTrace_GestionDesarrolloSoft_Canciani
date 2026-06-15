import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  getMisEquipos,
  getAsignaciones,
  asignacionMasiva,
  clonarEquipo,
  modificarVigencia,
  getMisMaterias,
  searchUsuarios,
  updateAsignacion,
  type PaginatedResponse,
} from '@/features/coordinacion/equipos/services/equipos.service';

import type {
  AsignacionResponse,
  EquiposFilters,
  AsignacionesFilters,
  AsignacionMasivaPayload,
  ClonarEquipoPayload,
  VigenciaPayload,
  MisMateria,
  UsuarioSearchResult,
} from '@/features/coordinacion/equipos/types/equipos.types';

export function useMisEquipos(filters?: EquiposFilters) {
  return useQuery<PaginatedResponse<AsignacionResponse>>({
    queryKey: ['mis-equipos', filters],
    queryFn: () => getMisEquipos(filters),
  });
}

export function useAsignaciones(page: number, filters?: AsignacionesFilters) {
  return useQuery<PaginatedResponse<AsignacionResponse>>({
    queryKey: ['asignaciones', page, filters],
    queryFn: () => getAsignaciones(page, filters),
  });
}

export function useAsignacionMasiva() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AsignacionMasivaPayload) => asignacionMasiva(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mis-equipos'] });
      queryClient.invalidateQueries({ queryKey: ['asignaciones'] });
    },
  });
}

export function useClonarEquipo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ClonarEquipoPayload) => clonarEquipo(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mis-equipos'] });
      queryClient.invalidateQueries({ queryKey: ['asignaciones'] });
    },
  });
}

export function useModificarVigencia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: VigenciaPayload) => modificarVigencia(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mis-equipos'] });
      queryClient.invalidateQueries({ queryKey: ['asignaciones'] });
    },
  });
}

export function useMisMaterias() {
  return useQuery<MisMateria[]>({
    queryKey: ['mis-materias'],
    queryFn: () => getMisMaterias(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useSearchUsuarios(q: string) {
  return useQuery<PaginatedResponse<UsuarioSearchResult>>({
    queryKey: ['search-usuarios', q],
    queryFn: () => searchUsuarios(q),
    enabled: q.length >= 2,
  });
}

export function useUpdateAsignacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
      updateAsignacion(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['asignaciones'] });
      queryClient.invalidateQueries({ queryKey: ['mis-equipos'] });
    },
  });
}
