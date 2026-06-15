import { DataTable } from '@/shared/components/ui/DataTable';

import type { LogEntry } from '@/features/admin/types/auditoria.types';
import type { Column } from '@/shared/components/ui/DataTable';

interface UltimasAccionesProps {
  data: LogEntry[];
  isLoading: boolean;
}

export function UltimasAcciones({ data, isLoading }: UltimasAccionesProps) {
  const columns: Column[] = [
    { key: 'fecha_hora', header: 'Fecha/Hora' },
    { key: 'actor_nombre', header: 'Usuario' },
    {
      key: 'materia_nombre', header: 'Materia',
      render: (item) => (item.materia_nombre as string | null) ?? '—',
    },
    { key: 'accion', header: 'Acción' },
    { key: 'filas_afectadas', header: 'Filas' },
  ];

  return (
    <div>
      <h4 className="mb-3 text-sm font-medium text-secondary-700">Últimas Acciones</h4>
      <DataTable
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id as string}
        isLoading={isLoading}
        emptyMessage="Sin acciones registradas"
      />
    </div>
  );
}
