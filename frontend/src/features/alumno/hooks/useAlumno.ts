import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  getEstadoAcademico,
  getMisAvisos,
  confirmarAviso,
  getMisReservas,
  reservarColoquio,
  cancelarReserva,
} from '@/features/alumno/services/alumno.service';

export function useEstadoAcademico() {
  return useQuery({
    queryKey: ['alumno', 'estado-academico'],
    queryFn: getEstadoAcademico,
  });
}

export function useMisAvisos(page: number) {
  return useQuery({
    queryKey: ['alumno', 'avisos', page],
    queryFn: () => getMisAvisos(page),
  });
}

export function useConfirmarAviso() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: confirmarAviso,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alumno', 'avisos'] });
    },
  });
}

export function useMisReservas() {
  return useQuery({
    queryKey: ['alumno', 'coloquios', 'mis-reservas'],
    queryFn: getMisReservas,
  });
}

export function useReservarColoquio() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ evaluacionId, fecha_hora }: { evaluacionId: string; fecha_hora: string }) =>
      reservarColoquio(evaluacionId, fecha_hora),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alumno', 'coloquios'] });
    },
  });
}

export function useCancelarReserva() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelarReserva,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alumno', 'coloquios'] });
    },
  });
}
