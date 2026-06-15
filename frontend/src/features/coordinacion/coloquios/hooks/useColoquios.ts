import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  getMetricas,
  getConvocatorias,
  crearConvocatoria,
  importarAlumnos,
  getReservas,
  getRegistroAcademico,
} from '@/features/coordinacion/coloquios/services/coloquios.service';

import type {
  ColoquioMetricas,
  Convocatoria,
  ConvocatoriaFormData,
  AgendaReserva,
  AgendaReservasFilters,
  RegistroAcademicoRow,
} from '@/features/coordinacion/coloquios/types/coloquios.types';

export function useColoquioMetricas() {
  return useQuery<ColoquioMetricas>({
    queryKey: ['coloquio-metricas'],
    queryFn: getMetricas,
  });
}

export function useConvocatorias() {
  return useQuery<Convocatoria[]>({
    queryKey: ['convocatorias'],
    queryFn: getConvocatorias,
  });
}

export function useCrearConvocatoria() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ConvocatoriaFormData) => crearConvocatoria(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['convocatorias'] });
      queryClient.invalidateQueries({ queryKey: ['coloquio-metricas'] });
    },
  });
}

export function useImportarAlumnos() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ convocatoriaId, archivo }: { convocatoriaId: string; archivo: File }) =>
      importarAlumnos(convocatoriaId, archivo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['convocatorias'] });
    },
  });
}

export function useReservas(filters?: AgendaReservasFilters) {
  return useQuery<AgendaReserva[]>({
    queryKey: ['reservas', filters],
    queryFn: () => getReservas(filters),
  });
}

export function useRegistroAcademico() {
  return useQuery<RegistroAcademicoRow[]>({
    queryKey: ['registro-academico'],
    queryFn: getRegistroAcademico,
  });
}
