import { useQuery, useMutation } from '@tanstack/react-query';

import {
  uploadReporteFinalizacion,
  getEntregasSinCorregir,
  exportEntregasSinCorregir,
} from '@/features/academico/services/analisis.service';

import type { EntradaMonitor } from '@/features/academico/types/analisis.types';

export function useUploadReporteFinalizacion() {
  return useMutation({
    mutationFn: ({ formData, onProgress }: { formData: FormData; onProgress?: (pct: number) => void }) =>
      uploadReporteFinalizacion(formData, onProgress),
  });
}

export function useEntregasSinCorregir(materiaId: string) {
  return useQuery<EntradaMonitor[]>({
    queryKey: ['analisis', 'entregas-sin-corregir', materiaId],
    queryFn: () => getEntregasSinCorregir(materiaId),
    enabled: !!materiaId,
  });
}

export function useExportEntregasSinCorregir() {
  return useMutation({
    mutationFn: (materiaId: string) => exportEntregasSinCorregir(materiaId),
  });
}
