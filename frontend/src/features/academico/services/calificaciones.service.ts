import api from '@/shared/services/api';

import type { PreviewResponse, UmbralConfig } from '@/features/academico/types/calificaciones.types';

export async function uploadCalificaciones(formData: FormData, onProgress?: (pct: number) => void): Promise<PreviewResponse> {
  const { data } = await api.post('/v1/calificaciones/importar/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
  return data;
}

export async function confirmarImportacion(materiaId: string, actividades: string[]): Promise<void> {
  await api.post('/v1/calificaciones/importar/confirmar', { materia_id: materiaId, actividades });
}

// Backend no tiene endpoint de preview GET; se usa solo el resultado del upload
export async function getPreview(_materiaId: string): Promise<PreviewResponse> {
  return { actividades: [], totalAlumnos: 0, materiaId: _materiaId, materiaNombre: '' };
}

export async function getUmbral(materiaId: string): Promise<UmbralConfig> {
  const { data } = await api.get('/v1/calificaciones/umbral', {
    params: { materia_id: materiaId },
  });
  return {
    materiaId: data.materia_id,
    porcentaje: data.umbral_pct,
    tieneCalificaciones: false,
  };
}

export async function setUmbral(materiaId: string, porcentaje: number): Promise<UmbralConfig> {
  const { data } = await api.put(
    '/v1/calificaciones/umbral',
    { umbral_pct: porcentaje },
    { params: { materia_id: materiaId } },
  );
  return {
    materiaId: data.materia_id,
    porcentaje: data.umbral_pct,
    tieneCalificaciones: false,
  };
}
