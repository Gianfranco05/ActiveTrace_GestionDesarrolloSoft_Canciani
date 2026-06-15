import { MateriaSelector } from '@/features/academico/components/MateriaSelector';
import { useMateriaSeleccionada } from '@/features/academico/hooks/useMateriaSeleccionada';
import { useRanking } from '@/features/academico/hooks/useRanking';
import { Alert } from '@/shared/components/ui/Alert';
import { Card } from '@/shared/components/ui/Card';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { Spinner } from '@/shared/components/ui/Spinner';

export function RankingPage() {
  const [materiaId, setMateriaId] = useMateriaSeleccionada();
  const { data: ranking, isLoading, error } = useRanking(materiaId);

  const columns: Column[] = [
    { key: 'nombre', header: 'Alumno', sortable: true },
    {
      key: 'aprobadas',
      header: 'Aprobadas',
      sortable: true,
      render: (item) => `${item.aprobadas}/${item.total_actividades}`,
    },
    {
      key: 'porcentaje',
      header: '%',
      sortable: true,
      render: (item) => (
        <span className={Number(item.porcentaje) < 60 ? 'text-danger-600 font-medium' : ''}>
          {Number(item.porcentaje).toFixed(0)}%
        </span>
      ),
    },
  ];

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Ranking de Actividades</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Alumnos ordenados por cantidad de actividades aprobadas
        </p>
      </div>

      <Card>
        <div className="space-y-4">
          <MateriaSelector value={materiaId} onChange={setMateriaId} />

          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Spinner size="lg" />
            </div>
          )}

          {error && (
            <Alert variant="error">
              Error al cargar el ranking
            </Alert>
          )}

          {ranking && (
            <DataTable
              columns={columns}
              data={ranking}
                keyExtractor={(r) => r.entrada_padron_id}
              pageSize={20}
              emptyMessage="No hay datos de ranking para esta materia"
            />
          )}

          {!materiaId && (
            <p className="py-4 text-center text-sm text-secondary-400">
              Seleccioná una materia para ver el ranking
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
