import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';

import type { EstadoComunicacion } from '@/features/academico/types/comunicaciones.types';

interface ComunicacionTrackerProps {
  estados: EstadoComunicacion[];
  allInFinalState: boolean;
}

export function ComunicacionTracker({ estados, allInFinalState }: ComunicacionTrackerProps) {
  const counts = {
    Pendiente: estados.filter((e) => e.estado === 'Pendiente').length,
    Enviando: estados.filter((e) => e.estado === 'Enviando').length,
    Enviado: estados.filter((e) => e.estado === 'Enviado').length,
    Error: estados.filter((e) => e.estado === 'Error').length,
    Cancelado: estados.filter((e) => e.estado === 'Cancelado').length,
  };

  const columns: Column[] = [
    { key: 'destinatario', header: 'Destinatario', sortable: true },
    {
      key: 'estado',
      header: 'Estado',
      sortable: true,
      render: (item) => <StatusBadge status={item.estado} />,
    },
    {
      key: 'fechaEnvio',
      header: 'Fecha',
      sortable: true,
      render: (item) => item.fechaEnvio ?? '—',
    },
  ];

  return (
    <div>
      {allInFinalState && (
        <div className="mb-4 rounded-lg bg-green-50 p-3 text-sm text-green-800">
          Todas las comunicaciones fueron procesadas
        </div>
      )}

      <div className="mb-4 flex flex-wrap gap-3">
        {Object.entries(counts).map(([estado, count]) => (
          <span key={estado} className="text-sm text-secondary-600">
            <span className="font-medium">{estado}:</span> {count}
          </span>
        ))}
      </div>

      <DataTable
        columns={columns}
        data={estados}
        keyExtractor={(e) => e.id}
        pageSize={15}
        emptyMessage="No hay comunicaciones registradas"
      />
    </div>
  );
}
