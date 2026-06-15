import { Card } from '@/shared/components/ui/Card';

import type { ComunicacionPreview as ComunicacionPreviewType } from '@/features/academico/types/comunicaciones.types';

interface ComunicacionPreviewProps {
  items: ComunicacionPreviewType[];
}

export function ComunicacionPreview({ items }: ComunicacionPreviewProps) {
  if (items.length === 0) {
    return (
      <p className="py-4 text-center text-sm text-secondary-500">
        No hay comunicaciones para previsualizar
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-secondary-500">
        Se enviarán {items.length} comunicaciones
      </p>
      {items.map((item) => (
        <Card key={item.alumnoId} padding={false}>
          <div className="border-b border-secondary-200 bg-secondary-50 px-4 py-2">
            <span className="text-sm font-medium text-secondary-900">{item.alumnoNombre}</span>
            <span className="ml-2 text-xs text-secondary-400">{item.destinatario}</span>
          </div>
          <div className="px-4 py-3">
            <p className="text-xs font-semibold text-secondary-700">Asunto:</p>
            <p className="mb-2 text-sm text-secondary-600">{item.asunto}</p>
            <p className="text-xs font-semibold text-secondary-700">Cuerpo:</p>
            <p className="text-sm text-secondary-600 whitespace-pre-wrap">{item.cuerpo}</p>
          </div>
        </Card>
      ))}
    </div>
  );
}
