import { Link } from 'react-router-dom';

import { useHistorialLiquidaciones } from '@/features/finanzas/hooks/useHistorialLiquidaciones';
import { Button } from '@/shared/components/ui/Button';
import { DataTable } from '@/shared/components/ui/DataTable';
import { Spinner } from '@/shared/components/ui/Spinner';

import type { Column } from '@/shared/components/ui/DataTable';

export function HistorialLiquidacionesPage() {
  const { data, isLoading } = useHistorialLiquidaciones();

  const columns: Column[] = [
    { key: 'periodo', header: 'Período' },
    { key: 'cohorte_nombre', header: 'Cohorte' },
    {
      key: 'total_liquidado', header: 'Total Liquidado',
      render: (item) => (item.total_liquidado as number).toLocaleString('es-AR', { style: 'currency', currency: 'ARS' }),
    },
    { key: 'cantidad_docentes', header: 'Docentes' },
    { key: 'fecha_cierre', header: 'Fecha de Cierre' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Historial de Liquidaciones</h1>
          <p className="mt-1 text-sm text-secondary-500">Liquidaciones cerradas de períodos anteriores</p>
        </div>
        <Link to="/finanzas/liquidaciones">
          <Button variant="secondary" size="sm">Volver</Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Spinner size="lg" />
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={data ?? []}
          keyExtractor={(item) => item.id as string}
          emptyMessage="No hay liquidaciones cerradas"
        />
      )}
    </div>
  );
}
