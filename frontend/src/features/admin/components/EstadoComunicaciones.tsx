import { DataTable } from '@/shared/components/ui/DataTable';

import type { EstadoComunicacion } from '@/features/admin/types/auditoria.types';
import type { Column } from '@/shared/components/ui/DataTable';

interface EstadoComunicacionesProps {
  data: EstadoComunicacion[];
  isLoading: boolean;
}

export function EstadoComunicaciones({ data, isLoading }: EstadoComunicacionesProps) {
  const columns: Column[] = [
    { key: 'usuario_nombre', header: 'Docente' },
    {
      key: 'pendiente', header: 'Pend.',
      render: (item) => <span className="font-medium text-amber-600">{item.pendiente as number}</span>,
    },
    {
      key: 'enviando', header: 'Enviando',
      render: (item) => <span className="font-medium text-blue-600">{item.enviando as number}</span>,
    },
    {
      key: 'enviado', header: 'Enviado',
      render: (item) => <span className="font-medium text-green-600">{item.enviado as number}</span>,
    },
    {
      key: 'error', header: 'Error',
      render: (item) => <span className="font-medium text-danger-600">{item.error as number}</span>,
    },
    {
      key: 'cancelado', header: 'Canc.',
      render: (item) => <span className="font-medium text-secondary-500">{item.cancelado as number}</span>,
    },
  ];

  return (
    <div>
      <h4 className="mb-3 text-sm font-medium text-secondary-700">Estado de Comunicaciones</h4>
      <DataTable
        columns={columns}
        data={data}
        keyExtractor={(item) => item.usuario_id as string}
        isLoading={isLoading}
        emptyMessage="Sin datos de comunicaciones"
      />
    </div>
  );
}
