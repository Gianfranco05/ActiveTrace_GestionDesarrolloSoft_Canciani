import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  getTareas,
  getTarea,
  crearTarea,
  cambiarEstadoTarea,
  getComentarios,
  agregarComentario,
  getHistorial,
  type PaginatedResponse,
} from '@/features/coordinacion/tareas/services/tareas.service';

import type {
  Tarea,
  TareaFormData,
  TareaEstado,
  TareaComentario,
  TareaHistorial,
  TareasFilters,
} from '@/features/coordinacion/tareas/types/tareas.types';

export function useTareas(page: number, filters?: TareasFilters) {
  return useQuery<PaginatedResponse<Tarea>>({
    queryKey: ['tareas', page, filters],
    queryFn: () => getTareas(page, filters),
  });
}

export function useTarea(id: string) {
  return useQuery<Tarea>({
    queryKey: ['tarea', id],
    queryFn: () => getTarea(id),
    enabled: !!id,
  });
}

export function useCrearTarea() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TareaFormData) => crearTarea(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tareas'] });
    },
  });
}

export function useCambiarEstadoTarea() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, estado }: { id: string; estado: TareaEstado }) => cambiarEstadoTarea(id, estado),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tareas'] });
      queryClient.invalidateQueries({ queryKey: ['tarea', variables.id] });
    },
  });
}

export function useComentarios(tareaId: string) {
  return useQuery<TareaComentario[]>({
    queryKey: ['comentarios', tareaId],
    queryFn: () => getComentarios(tareaId),
    enabled: !!tareaId,
  });
}

export function useAgregarComentario() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ tareaId, contenido }: { tareaId: string; contenido: string }) =>
      agregarComentario(tareaId, contenido),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['comentarios', variables.tareaId] });
    },
  });
}

export function useHistorial(tareaId: string) {
  return useQuery<TareaHistorial[]>({
    queryKey: ['historial', tareaId],
    queryFn: () => getHistorial(tareaId),
    enabled: !!tareaId,
  });
}
