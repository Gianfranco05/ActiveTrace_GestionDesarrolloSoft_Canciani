import type { Column } from '@/shared/components/ui/DataTable';
import type { MateriaEstado } from '@/features/alumno/types/alumno.types';

import { useEstadoAcademico } from '@/features/alumno/hooks/useAlumno';
import { Card } from '@/shared/components/ui/Card';
import { DataTable } from '@/shared/components/ui/DataTable';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';

const columns: Column[] = [
  {
    key: 'materia_nombre',
    header: 'Materia',
    sortable: true,
    render: (item: MateriaEstado) => (
      <span className="font-medium">{item.materia_nombre}</span>
    ),
  },
  {
    key: 'carrera_nombre',
    header: 'Carrera',
    sortable: true,
  },
  {
    key: 'cohorte_nombre',
    header: 'Cohorte',
    sortable: true,
  },
  {
    key: 'porcentaje_aprobacion',
    header: '% Aprobación',
    sortable: true,
    render: (item: MateriaEstado) => {
      const pct = item.porcentaje_aprobacion;
      return (
        <div className="flex items-center gap-2">
          <div className="h-2 w-20 overflow-hidden rounded-full bg-secondary-200">
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${Math.min(100, pct)}%`, backgroundColor: pct >= 60 ? '#10b981' : pct >= 30 ? '#f59e0b' : '#ef4444' }}
            />
          </div>
          <span className="text-xs font-medium text-secondary-600">{pct}%</span>
        </div>
      );
    },
  },
  {
    key: 'estado',
    header: 'Estado',
    sortable: true,
    render: (item: MateriaEstado) => (
      <StatusBadge
        status={item.estado}
      />
    ),
  },
];

export function EstadoAcademicoPage() {
  const { data: estado, isLoading, isError } = useEstadoAcademico();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center py-20">
        <Card className="max-w-md">
          <p className="text-sm text-secondary-500 text-center py-4">
            No se pudo cargar el estado académico. Intentá de nuevo más tarde.
          </p>
        </Card>
      </div>
    );
  }

  if (!estado || estado.materias.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Estado Académico</h1>
          <p className="mt-1 text-sm text-secondary-500">
            Consultá tu progreso en cada materia.
          </p>
        </div>
        <Card>
          <p className="text-sm text-secondary-500 py-8 text-center">
            Todavía no tenés materias registradas. Si creés que esto es un error, contactá a tu coordinador.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Estado Académico</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Consultá tu progreso en cada materia.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <div className="text-center">
            <p className="text-3xl font-bold text-primary-600">{estado.resumen.materias_totales}</p>
            <p className="mt-1 text-sm text-secondary-500">Total materias</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-3xl font-bold text-success-600">{estado.resumen.materias_regulares}</p>
            <p className="mt-1 text-sm text-secondary-500">Regulares</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-3xl font-bold text-danger-600">{estado.resumen.materias_en_riesgo}</p>
            <p className="mt-1 text-sm text-secondary-500">En riesgo</p>
          </div>
        </Card>
      </div>

      <Card padding={false}>
        <div className="p-6">
          <DataTable<MateriaEstado>
            columns={columns}
            data={estado.materias}
            keyExtractor={(item) => item.materia_id}
            emptyMessage="No se encontraron materias"
          />
        </div>
      </Card>
    </div>
  );
}
