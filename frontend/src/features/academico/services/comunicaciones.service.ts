import api from '@/shared/services/api';

import type { ComunicacionPreview, EstadoComunicacion } from '@/features/academico/types/comunicaciones.types';

interface EnviarPayload {
  alumnosIds: string[];
  materiaId: string;
}

interface EnviarResponse {
  loteId: string;
}

export async function getPreview(alumnosIds: string[]): Promise<ComunicacionPreview[]> {
  const { data } = await api.post('/comunicaciones/preview', { alumnos_ids: alumnosIds });
  return data;
}

export async function enviarComunicacion(payload: EnviarPayload): Promise<EnviarResponse> {
  const { data } = await api.post('/comunicaciones/enviar', {
    alumnos_ids: payload.alumnosIds,
    materia_id: payload.materiaId,
  });
  return data;
}

export async function getEstadoComunicaciones(loteId: string): Promise<EstadoComunicacion[]> {
  const { data } = await api.get(`/comunicaciones/estado/${loteId}`);
  return data;
}

export async function cancelarComunicacion(loteId: string): Promise<void> {
  await api.post(`/comunicaciones/cancelar/${loteId}`);
}
