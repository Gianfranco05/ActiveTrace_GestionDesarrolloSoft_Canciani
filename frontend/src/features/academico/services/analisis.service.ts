import api from '@/shared/services/api';

import type { AlumnoAtrasado, RankingItem, NotaFinal, MetricaReporte, EntradaMonitor } from '@/features/academico/types/analisis.types';

export async function getAtrasados(materiaId: string, filtros?: { minFaltantes?: number; maxPorcentaje?: number }): Promise<AlumnoAtrasado[]> {
  const params: Record<string, string | number> = { materia_id: materiaId };
  if (filtros?.minFaltantes) params.min_faltantes = filtros.minFaltantes;
  if (filtros?.maxPorcentaje) params.max_porcentaje = filtros.maxPorcentaje;
  const { data } = await api.get('/analisis/atrasados', { params });
  return data.items ?? data;
}

export async function getRanking(materiaId: string): Promise<RankingItem[]> {
  const { data } = await api.get('/analisis/ranking', { params: { materia_id: materiaId } });
  return data.items ?? data;
}

export async function getNotasFinales(materiaId: string): Promise<NotaFinal[]> {
  const { data } = await api.get('/analisis/notas-finales', { params: { materia_id: materiaId } });
  return data.items ?? data;
}

export async function getReportesRapidos(materiaId: string): Promise<MetricaReporte> {
  const { data } = await api.get(`/analisis/reportes/materia/${materiaId}`);
  return data;
}

export async function getMonitores(filtros: Record<string, string | number | undefined>): Promise<EntradaMonitor[]> {
  const params: Record<string, string | number> = {};
  for (const [key, val] of Object.entries(filtros)) {
    if (val !== undefined) params[key] = val;
  }
  const { data } = await api.get('/analisis/monitor/general', { params });
  return data;
}

export async function uploadReporteFinalizacion(formData: FormData, onProgress?: (pct: number) => void): Promise<{ alumnosSinCorregir: number }> {
  const { data } = await api.post('/analisis/reporte-finalizacion', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
  return data;
}

export async function getEntregasSinCorregir(materiaId: string): Promise<EntradaMonitor[]> {
  const { data } = await api.get('/analisis/export/tps-sin-corregir', { params: { materia_id: materiaId } });
  return data;
}

export async function exportEntregasSinCorregir(materiaId: string): Promise<void> {
  const response = await api.get('/analisis/export/tps-sin-corregir', {
    params: { materia_id: materiaId },
    responseType: 'blob',
  });
  const url = URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.download = `entregas-sin-corregir-${materiaId}.xlsx`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function exportNotasFinales(materiaId: string): Promise<void> {
  const response = await api.get('/analisis/notas-finales/exportar', {
    params: { materia_id: materiaId },
    responseType: 'blob',
  });
  const url = URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.download = `notas-finales-${materiaId}.xlsx`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
