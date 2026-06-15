import { useState } from 'react';

import { FiltrosMonitor } from '@/features/academico/components/FiltrosMonitor';
import { MateriaSelector } from '@/features/academico/components/MateriaSelector';
import { useMateriaSeleccionada } from '@/features/academico/hooks/useMateriaSeleccionada';
import { useMonitores } from '@/features/academico/hooks/useMonitores';
import { Alert } from '@/shared/components/ui/Alert';
import { Card } from '@/shared/components/ui/Card';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';
import { useAuth } from '@/shared/hooks/useAuth';

export function MonitoresSeguimientoPage() {
  const [materiaId, setMateriaId] = useMateriaSeleccionada();
  const { roles } = useAuth();
  const [filtros, setFiltros] = useState<Record<string, string>>({});

  const showDateFilters = roles.some((r) => r === 'COORDINADOR' || r === 'ADMIN');

  const queryFiltros: Record<string, string | number | undefined> = {};
  if (materiaId) queryFiltros.materia_id = materiaId;
  for (const [key, val] of Object.entries(filtros)) {
    if (val) {
      queryFiltros[key] = key === 'minActividades' ? parseInt(val, 10) : val;
    }
  }

  const { data: monitores, isLoading, error } = useMonitores(queryFiltros);

  const columns: Column[] = [
    { key: 'alumnoNombre', header: 'Alumno', sortable: true },
    { key: 'actividad', header: 'Actividad', sortable: true },
    {
      key: 'estado',
      header: 'Estado',
      sortable: true,
      render: (item) => <StatusBadge status={item.estado} />,
    },
    {
      key: 'fecha',
      header: 'Fecha',
      sortable: true,
      render: (item) => item.fecha ?? '—',
    },
  ];

  const handleFiltroChange = (key: string, value: string) => {
    setFiltros((prev) => ({ ...prev, [key]: value }));
  };

  const handleLimpiarFiltros = () => {
    setFiltros({});
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Monitores de Seguimiento</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Seguimiento del estado de actividades por alumno
        </p>
      </div>

      <Card>
        <div className="space-y-4">
          <MateriaSelector
            value={materiaId}
            onChange={(id) => {
              setMateriaId(id);
              handleLimpiarFiltros();
            }}
          />

          <FiltrosMonitor
            filtros={filtros}
            onChange={handleFiltroChange}
            onLimpiar={handleLimpiarFiltros}
            showDateFilters={showDateFilters}
          />

          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Spinner size="lg" />
            </div>
          )}

          {error && (
            <Alert variant="error">
              Error al cargar los datos del monitor
            </Alert>
          )}

          {monitores && (
            <DataTable
              columns={columns}
              data={monitores}
              keyExtractor={(e, i) => `${e.alumno_id}-${e.actividad}-${i}`}
              pageSize={20}
              emptyMessage="No se encontraron registros con los filtros seleccionados"
            />
          )}

          {!materiaId && (
            <p className="py-4 text-center text-sm text-secondary-400">
              Seleccioná una materia para ver el monitor
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
