import { DataTable } from '@/shared/components/ui/DataTable';

import type { AccionPorDia } from '@/features/admin/types/auditoria.types';
import type { Column } from '@/shared/components/ui/DataTable';

interface AccionesPorDiaProps {
  data: AccionPorDia[];
  isLoading: boolean;
}

export function AccionesPorDia({ data, isLoading }: AccionesPorDiaProps) {
  const columns: Column[] = [
    { key: 'dia', header: 'Fecha' },
    {
      key: 'total_acciones', header: 'Acciones',
      className: 'font-semibold',
    },
  ];

  return (
    <div>
      <h4 className="mb-3 text-sm font-medium text-secondary-700">Acciones por Día</h4>
      <DataTable
        columns={columns}
        data={data}
        keyExtractor={(item) => item.dia as string}
        isLoading={isLoading}
        emptyMessage="Sin datos de actividad"
      />
    </div>
  );
}
