import api from '@/shared/services/api';

import type {
  CrearCohortePayload,
  Cohorte,
  SetupClonePayload,
  FechaEvaluacionPayload,
  FechaEvaluacion,
} from '@/features/coordinacion/setup/types/setup.types';

export async function crearCohorte(payload: CrearCohortePayload): Promise<Cohorte> {
  const { data } = await api.post('/cohortes', payload);
  return data;
}

export async function clonarEquipoSetup(payload: SetupClonePayload): Promise<{ asignaciones_creadas: number }> {
  const { data } = await api.post('/setup/clonar-equipo', payload);
  return data;
}

export async function cargarPrograma(materiaId: string, titulo: string, archivo: File): Promise<void> {
  const formData = new FormData();
  formData.append('archivo', archivo);
  formData.append('titulo', titulo);
  await api.post(`/setup/programas/${materiaId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export async function getFechasEvaluaciones(cohorteId: string): Promise<FechaEvaluacion[]> {
  const { data } = await api.get(`/setup/fechas-evaluaciones`, { params: { cohorte_id: cohorteId } });
  return data;
}

export async function crearFechaEvaluacion(payload: FechaEvaluacionPayload): Promise<FechaEvaluacion> {
  const { data } = await api.post('/setup/fechas-evaluaciones', payload);
  return data;
}

export async function eliminarFechaEvaluacion(id: string): Promise<void> {
  await api.delete(`/setup/fechas-evaluaciones/${id}`);
}

export async function getCohortes(): Promise<Cohorte[]> {
  const { data } = await api.get('/cohortes');
  return data;
}

export async function getCohorte(id: string): Promise<Cohorte> {
  const { data } = await api.get(`/cohortes/${id}`);
  return data;
}
