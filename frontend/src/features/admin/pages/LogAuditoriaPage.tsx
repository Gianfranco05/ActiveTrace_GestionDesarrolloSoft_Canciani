import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';

import { useLogAuditoria } from '@/features/admin/hooks/useAuditoria';
import { Button } from '@/shared/components/ui/Button';
import { DataTable } from '@/shared/components/ui/DataTable';
import { Input } from '@/shared/components/ui/Input';
import { Spinner } from '@/shared/components/ui/Spinner';

import type { Column } from '@/shared/components/ui/DataTable';


const PAGE_SIZE = 50;

export function LogAuditoriaPage() {
  const [page, setPage] = useState(1);
  const [accion, setAccion] = useState('');
  const [usuarioId, setUsuarioId] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');

  const filter = useMemo(
    () => ({
      offset: (page - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
      accion: accion || undefined,
      usuario_id: usuarioId || undefined,
      fecha_desde: fechaDesde || undefined,
      fecha_hasta: fechaHasta || undefined,
    }),
    [page, accion, usuarioId, fechaDesde, fechaHasta]
  );

  const { data, isLoading } = useLogAuditoria(filter);

  const columns: Column[] = [
    { key: 'fecha_hora', header: 'Fecha/Hora' },
    { key: 'actor_nombre', header: 'Usuario' },
    {
      key: 'materia_nombre', header: 'Materia',
      render: (item) => (item.materia_nombre as string | null) ?? '—',
    },
    { key: 'accion', header: 'Acción' },
    { key: 'filas_afectadas', header: 'Filas' },
    { key: 'ip', header: 'IP' },
    { key: 'user_agent', header: 'User Agent' },
  ];

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.limit)) : 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Log de Auditoría</h1>
          <p className="mt-1 text-sm text-secondary-500">Registro completo de acciones del sistema</p>
        </div>
        <Link to="/admin/auditoria">
          <Button variant="secondary" size="sm">Volver al Panel</Button>
        </Link>
      </div>

      <div className="flex flex-wrap gap-4 rounded-lg border border-secondary-200 bg-white p-4">
        <div className="w-48">
          <Input
            label="Acción"
            placeholder="LIQUIDACION_CERRAR..."
            value={accion}
            onChange={(e) => { setAccion(e.target.value); setPage(1); }}
          />
        </div>
        <div className="w-48">
          <Input
            label="Usuario ID"
            placeholder="Filtrar por usuario..."
            value={usuarioId}
            onChange={(e) => { setUsuarioId(e.target.value); setPage(1); }}
          />
        </div>
        <div className="w-44">
          <Input
            label="Fecha desde"
            type="date"
            value={fechaDesde}
            onChange={(e) => { setFechaDesde(e.target.value); setPage(1); }}
          />
        </div>
        <div className="w-44">
          <Input
            label="Fecha hasta"
            type="date"
            value={fechaHasta}
            onChange={(e) => { setFechaHasta(e.target.value); setPage(1); }}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8"><Spinner size="lg" /></div>
      ) : (
        <>
          <DataTable
            columns={columns}
            data={data?.items ?? []}
            keyExtractor={(item) => item.id as string}
            emptyMessage="No se encontraron registros de auditoría"
          />

          <div className="flex items-center justify-between">
            <p className="text-sm text-secondary-500">
              Página {page} de {totalPages} — {(data?.total ?? 0)} registros
            </p>
            <div className="flex gap-2">
              <Button
                variant="secondary" size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Anterior
              </Button>
              <Button
                variant="secondary" size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
