import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { uploadCalificaciones, getPreview, confirmarImportacion } from '@/features/academico/services/calificaciones.service';

import type { PreviewResponse } from '@/features/academico/types/calificaciones.types';

export function useUploadCalificaciones() {
  return useMutation({
    mutationFn: ({ formData, onProgress }: { formData: FormData; onProgress?: (pct: number) => void }) =>
      uploadCalificaciones(formData, onProgress),
  });
}

export function usePreview(materiaId: string) {
  return useQuery<PreviewResponse>({
    queryKey: ['calificaciones', 'preview', materiaId],
    queryFn: () => getPreview(materiaId),
    enabled: !!materiaId,
  });
}

export function useConfirmarImportacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ materiaId, actividades }: { materiaId: string; actividades: string[] }) =>
      confirmarImportacion(materiaId, actividades),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['calificaciones', 'preview', variables.materiaId] });
      queryClient.invalidateQueries({ queryKey: ['analisis'] });
    },
  });
}
