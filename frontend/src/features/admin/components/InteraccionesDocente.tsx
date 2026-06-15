import { DataTable } from '@/shared/components/ui/DataTable';

import type { InteraccionDocente } from '@/features/admin/types/auditoria.types';
import type { Column } from '@/shared/components/ui/DataTable';

interface InteraccionesDocenteProps {
  data: InteraccionDocente[];
  isLoading: boolean;
}

export function InteraccionesDocente({ data, isLoading }: InteraccionesDocenteProps) {
  const columns: Column[] = [
    { key: 'usuario_nombre', header: 'Docente' },
    { key: 'materia_nombre', header: 'Materia' },
    { key: 'accion', header: 'Tipo Acción' },
    { key: 'cantidad', header: 'Cantidad', className: 'font-semibold' },
  ];

  return (
    <div>
      <h4 className="mb-3 text-sm font-medium text-secondary-700">Interacciones por Docente</h4>
      <DataTable
        columns={columns}
        data={data}
        keyExtractor={(item) => `${item.usuario_id as string}-${item.materia_id as string}-${item.accion as string}`}
        isLoading={isLoading}
        emptyMessage="Sin datos de interacciones"
      />
    </div>
  );
}
