import { MateriaSelector } from '@/features/academico/components/MateriaSelector';
import { MetricasCards } from '@/features/academico/components/MetricasCards';
import { useMateriaSeleccionada } from '@/features/academico/hooks/useMateriaSeleccionada';
import { useReportes } from '@/features/academico/hooks/useReportes';
import { Alert } from '@/shared/components/ui/Alert';
import { Card } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';

export function ReportesPage() {
  const [materiaId, setMateriaId] = useMateriaSeleccionada();
  const { data: metricas, isLoading, error } = useReportes(materiaId);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Reportes Rápidos</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Resumen de métricas clave de la materia
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
              Error al cargar los reportes
            </Alert>
          )}

          {metricas && materiaId && (
            <MetricasCards metricas={metricas} materiaId={materiaId} />
          )}

          {!materiaId && (
            <p className="py-4 text-center text-sm text-secondary-400">
              Seleccioná una materia para ver sus reportes
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
