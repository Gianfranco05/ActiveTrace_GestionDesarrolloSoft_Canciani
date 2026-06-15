import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';

import type { AlumnoAtrasado } from '@/features/academico/types/analisis.types';

interface AtrasadosTableProps {
  atrasados: AlumnoAtrasado[];
  seleccionados: string[];
  onToggle: (id: string) => void;
  onToggleAll: () => void;
}

export function AtrasadosTable({ atrasados, seleccionados, onToggle, onToggleAll }: AtrasadosTableProps) {
  const allSelected = atrasados.length > 0 && seleccionados.length === atrasados.length;

  const columns: Column[] = [
    {
      key: 'seleccion',
      header: (
        <input
          type="checkbox"
          checked={allSelected}
          onChange={onToggleAll}
          className="h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
        />
      ),
      render: (item) => (
        <input
          type="checkbox"
          checked={seleccionados.includes(item.entrada_padron_id)}
          onChange={() => onToggle(item.entrada_padron_id)}
          className="h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
        />
      ),
    },
    { key: 'nombre', header: 'Alumno', sortable: true },
    {
      key: 'actividadesFaltantes',
      header: 'Faltantes',
      sortable: true,
      render: (item) => (
        <span>{item.actividadesFaltantes}/{item.totalActividades}</span>
      ),
    },
    {
      key: 'porcentajeAprobacion',
      header: '% Aprobación',
      sortable: true,
      render: (item) => (
        <span className={item.porcentajeAprobacion < 60 ? 'text-danger-600 font-medium' : ''}>
          {item.porcentajeAprobacion}%
        </span>
      ),
    },
    {
      key: 'estado',
      header: 'Estado',
      render: (item) => (
        <StatusBadge status={item.porcentajeAprobacion >= 60 ? 'Aprobado' : 'Desaprobado'} />
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={atrasados}
      keyExtractor={(a) => a.entrada_padron_id}
      pageSize={15}
      emptyMessage="No hay alumnos atrasados en esta materia"
    />
  );
}
