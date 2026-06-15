import { MateriaSelector } from '@/features/academico/components/MateriaSelector';
import { useMateriaSeleccionada } from '@/features/academico/hooks/useMateriaSeleccionada';
import { useNotasFinales } from '@/features/academico/hooks/useNotasFinales';
import { exportNotasFinales } from '@/features/academico/services/analisis.service';
import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';

export function NotasFinalesPage() {
  const [materiaId, setMateriaId] = useMateriaSeleccionada();
  const { data: notas, isLoading, error } = useNotasFinales(materiaId);

  const columns: Column[] = [
    { key: 'nombre', header: 'Alumno', sortable: true },
    {
      key: 'nota_promedio',
      header: 'Nota Final',
      sortable: true,
      render: (item) => item.nota_promedio != null ? Number(item.nota_promedio).toFixed(2) : '—',
    },
    {
      key: 'estado',
      header: 'Estado',
      sortable: true,
      render: (item) => <StatusBadge status={item.estado} />,
    },
  ];

  const handleExport = async () => {
    if (!materiaId || !notas || notas.length === 0) return;
    try {
      await exportNotasFinales(materiaId);
    } catch {
      // Error handled silently
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Notas Finales</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Notas finales calculadas por alumno
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
              Error al cargar las notas finales
            </Alert>
          )}

          {notas && (
            <>
              <DataTable
                columns={columns}
                data={notas}
                keyExtractor={(n) => n.entrada_padron_id}
                pageSize={20}
                emptyMessage="No hay notas finales calculadas para esta materia"
              />
              <Button
                variant="secondary"
                onClick={handleExport}
                disabled={notas.length === 0}
              >
                Exportar (.xlsx)
              </Button>
            </>
          )}

          {!materiaId && (
            <p className="py-4 text-center text-sm text-secondary-400">
              Seleccioná una materia para ver las notas finales
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
