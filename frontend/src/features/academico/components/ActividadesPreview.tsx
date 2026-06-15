import { DataTable, type Column } from '@/shared/components/ui/DataTable';

import type { ActividadDetectada } from '@/features/academico/types/calificaciones.types';

interface ActividadesPreviewProps {
  actividades: ActividadDetectada[];
  seleccionadas: string[];
  onToggle: (id: string) => void;
}

export function ActividadesPreview({ actividades, seleccionadas, onToggle }: ActividadesPreviewProps) {
  const columns: Column[] = [
    {
      key: 'seleccionada',
      header: 'Incluir',
      render: (item) => (
        <input
          type="checkbox"
          checked={seleccionadas.includes(item.id)}
          onChange={() => onToggle(item.id)}
          className="h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
        />
      ),
    },
    { key: 'nombre', header: 'Actividad', sortable: true },
    { key: 'fecha', header: 'Fecha', sortable: true },
    {
      key: 'alumnosCount',
      header: 'Alumnos',
      sortable: true,
      render: (item) => String(item.alumnosCount),
    },
  ];

  return (
    <div>
      <h3 className="mb-3 text-sm font-medium text-secondary-700">
        Actividades detectadas ({actividades.length})
      </h3>
      <DataTable
        columns={columns}
        data={actividades}
        keyExtractor={(a) => a.id}
        pageSize={10}
        emptyMessage="No se detectaron actividades en el archivo"
      />
    </div>
  );
}
