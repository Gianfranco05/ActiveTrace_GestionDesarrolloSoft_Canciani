import api from '@/shared/services/api';

import type { EstadoAcademico, AvisoAlumno } from '../types/alumno.types';

export async function getEstadoAcademico(): Promise<EstadoAcademico> {
  const { data } = await api.get('/v1/alumnos/estado-academico');
  return data;
}

export async function getMisAvisos(page: number): Promise<{ items: AvisoAlumno[]; total: number }> {
  const { data } = await api.get('/avisos', { params: { offset: (page - 1) * 20, limit: 20, activo: true } });
  return data;
}

export async function confirmarAviso(avisoId: string): Promise<void> {
  await api.post(`/avisos/${avisoId}/ack`);
}

export async function getMisReservas(): Promise<any[]> {
  const { data } = await api.get('/coloquios/mis-reservas');
  return data.items ?? data;
}

export async function reservarColoquio(evaluacionId: string, fecha_hora: string): Promise<any> {
  const { data } = await api.post(`/coloquios/${evaluacionId}/reservas`, { fecha_hora });
  return data;
}

export async function cancelarReserva(reservaId: string): Promise<any> {
  const { data } = await api.patch(`/coloquios/reservas/${reservaId}/cancelar`);
  return data;
}
