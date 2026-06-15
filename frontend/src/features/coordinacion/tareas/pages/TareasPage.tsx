import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { useTareas, useCambiarEstadoTarea } from '@/features/coordinacion/tareas/hooks/useTareas';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { Input } from '@/shared/components/ui/Input';
import { Pagination } from '@/shared/components/ui/Pagination';
import { Select } from '@/shared/components/ui/Select';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';

import type { TareasFilters, TareaEstado } from '@/features/coordinacion/tareas/types/tareas.types';

const estadoBadge: Record<TareaEstado, 'pending' | 'progress' | 'resolved' | 'cancelled'> = {
  'Pendiente': 'pending',
  'En progreso': 'progress',
  'Resuelta': 'resolved',
  'Cancelada': 'cancelled',
};

export function TareasPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<TareasFilters>({});
  const { data, isLoading } = useTareas(page, filters);
  const { mutateAsync: cambiarEstado } = useCambiarEstadoTarea();

  const columns = useMemo<Column[]>(
    () => [
      { key: 'titulo', header: 'Título' },
      {
        key: 'estado',
        header: 'Estado',
        render: (item: any) => <StatusBadge variant={estadoBadge[item.estado as TareaEstado]} label={item.estado} />,
      },
      { key: 'asignado_a_nombre', header: 'Docente Asignado' },
      { key: 'materia_nombre', header: 'Materia' },
      { key: 'created_at', header: 'Creado' },
      {
        key: 'acciones',
        header: 'Acciones',
        render: (item: any) => {
          const nextStates: { label: string; estado: TareaEstado }[] = [];
          if (item.estado === 'Pendiente') nextStates.push({ label: 'En progreso', estado: 'En progreso' });
          if (item.estado === 'En progreso') nextStates.push({ label: 'Resuelta', estado: 'Resuelta' });
          if (item.estado !== 'Cancelada' && item.estado !== 'Resuelta') nextStates.push({ label: 'Cancelar', estado: 'Cancelada' });

          return (
            <div className="flex gap-1">
              {nextStates.map((ns) => (
                <Button
                  key={ns.estado}
                  size="sm"
                  variant="ghost"
                  aria-label={`Cambiar estado a ${ns.label}`}
                  onClick={async (e) => { e.stopPropagation(); await cambiarEstado({ id: item.id, estado: ns.estado }); }}
                >
                  {ns.label}
                </Button>
              ))}
            </div>
          );
        },
      },
    ],
    [cambiarEstado]
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-secondary-900">Tareas</h1>
        <Link to="/coordinacion/tareas/nueva">
          <Button variant="primary" size="sm">Nueva Tarea</Button>
        </Link>
      </div>

      <Card>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Select
            label="Estado"
            options={[
              { value: '', label: 'Todos' },
              { value: 'Pendiente', label: 'Pendiente' },
              { value: 'En progreso', label: 'En progreso' },
              { value: 'Resuelta', label: 'Resuelta' },
              { value: 'Cancelada', label: 'Cancelada' },
            ]}
            value={filters.estado ?? ''}
            onChange={(e) => { setFilters((f) => ({ ...f, estado: (e.target.value || undefined) as TareaEstado })); setPage(1); }}
          />
          <Input label="Buscar" placeholder="Título..." value={filters.q ?? ''} onChange={(e) => { setFilters((f) => ({ ...f, q: e.target.value || undefined })); setPage(1); }} />
          <Input label="Materia ID" value={filters.materia_id ?? ''} onChange={(e) => { setFilters((f) => ({ ...f, materia_id: e.target.value || undefined })); setPage(1); }} />
        </div>
      </Card>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : (
        <>
          <Card>
            <DataTable
              columns={columns}
              data={data?.data ?? []}
              keyExtractor={(t) => t.id}
              onRowClick={(item) => window.location.href = `/coordinacion/tareas/${item.id}`}
            />
          </Card>
          {data && <Pagination page={data.page} totalPages={data.total_pages} onPageChange={setPage} />}
        </>
      )}
    </div>
  );
}
