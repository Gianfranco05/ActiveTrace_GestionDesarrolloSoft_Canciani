import { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { useAvisos, useEliminarAviso, useAcuses } from '@/features/coordinacion/avisos/hooks/useAvisos';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { ConfirmDialog } from '@/shared/components/ui/ConfirmDialog';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { Input } from '@/shared/components/ui/Input';
import { Modal } from '@/shared/components/ui/Modal';
import { Pagination } from '@/shared/components/ui/Pagination';
import { Select } from '@/shared/components/ui/Select';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';
import { useConfirmDialog } from '@/shared/hooks/useConfirmDialog';

import type { AvisosFilters } from '@/features/coordinacion/avisos/types/avisos.types';
import type { Aviso } from '@/features/coordinacion/avisos/types/avisos.types';

export function AvisosPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<AvisosFilters>({});
  const deleteDialog = useConfirmDialog<Aviso>();
  const [acusesModalId, setAcusesModalId] = useState<string | null>(null);

  const { data, isLoading } = useAvisos(page, filters);
  const { mutateAsync: eliminar } = useEliminarAviso();
  const { data: acuses, isLoading: acusesLoading } = useAcuses(acusesModalId ?? '');

  const handleDelete = useCallback(async () => {
    if (!deleteDialog.item) return;
    try {
      await eliminar(deleteDialog.item.id);
      toast.success('Aviso eliminado correctamente');
      deleteDialog.close();
    } catch {
      toast.error('Error al eliminar el aviso');
    }
  }, [deleteDialog, eliminar]);

  const columns = useMemo<Column[]>(
    () => [
      { key: 'titulo', header: 'Título' },
      {
        key: 'severidad',
        header: 'Severidad',
        render: (item) => {
          const variant =
            item.severidad === 'Critico'
              ? 'error'
              : item.severidad === 'Advertencia'
                ? 'warning'
                : 'info';
          return <StatusBadge variant={variant} label={item.severidad} />;
        },
      },
      { key: 'alcance', header: 'Alcance' },
      {
        key: 'activo',
        header: 'Estado',
        render: (item) => (
          <StatusBadge
            variant={item.activo ? 'active' : 'inactive'}
            label={item.activo ? 'Activo' : 'Inactivo'}
          />
        ),
      },
      { key: 'orden', header: 'Prioridad' },
      {
        key: 'acuses',
        header: 'Acuses',
        render: (item) =>
          item.requiere_ack
            ? `${item.acuses_confirmados ?? 0}/${item.total_acuses ?? 0}`
            : '—',
      },
      { key: 'created_at', header: 'Creado' },
      {
        key: 'acciones',
        header: 'Acciones',
        render: (item) => (
          <div className="flex gap-2">
            <Link to={`/coordinacion/avisos/${item.id}/editar`}>
              <Button size="sm" variant="ghost" aria-label={`Editar ${item.titulo}`}>
                Editar
              </Button>
            </Link>
            <Button
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation();
                deleteDialog.open(item);
              }}
              aria-label={`Eliminar ${item.titulo}`}
            >
              Eliminar
            </Button>
            {item.requiere_ack && (
              <Button
                size="sm"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  setAcusesModalId(item.id);
                }}
                aria-label={`Ver acuses de ${item.titulo}`}
              >
                Acuses
              </Button>
            )}
          </div>
        ),
      },
    ],
    [deleteDialog]
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-secondary-900">Avisos</h1>
        <Link to="/coordinacion/avisos/nuevo">
          <Button variant="primary" size="sm">
            Nuevo Aviso
          </Button>
        </Link>
      </div>

      <Card>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Select
            label="Estado"
            options={[
              { value: '', label: 'Todos' },
              { value: 'true', label: 'Activo' },
              { value: 'false', label: 'Inactivo' },
            ]}
            value={filters.activo === undefined ? '' : String(filters.activo)}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                activo:
                  e.target.value === ''
                    ? undefined
                    : e.target.value === 'true',
              }))
            }
          />
          <Select
            label="Alcance"
            options={[
              { value: '', label: 'Todos' },
              { value: 'Global', label: 'Global' },
              { value: 'PorMateria', label: 'Materia' },
              { value: 'PorCohorte', label: 'Cohorte' },
              { value: 'PorRol', label: 'Rol' },
            ]}
            value={filters.alcance ?? ''}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                alcance: (e.target.value || undefined) as AvisosFilters['alcance'],
              }))
            }
          />
          <Input
            label="Búsqueda"
            value={filters.busqueda ?? ''}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                busqueda: e.target.value || undefined,
              }))
            }
          />
        </div>
      </Card>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : (
        <>
          <Card>
            <DataTable
              columns={columns}
              data={data?.data ?? []}
              keyExtractor={(a) => a.id}
            />
          </Card>
          {data && (
            <Pagination
              page={data.page}
              totalPages={data.total_pages}
              onPageChange={setPage}
            />
          )}
        </>
      )}

      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        title="Eliminar Aviso"
        message={
          <span>
            ¿Estás seguro de eliminar el aviso "
            <strong>{deleteDialog.item?.titulo}</strong>"?
          </span>
        }
        confirmLabel="Eliminar"
        variant="danger"
        onConfirm={handleDelete}
        onCancel={deleteDialog.close}
      />

      <Modal
        isOpen={!!acusesModalId}
        onClose={() => setAcusesModalId(null)}
        title="Acuses de Recibo"
        size="lg"
      >
        {acusesLoading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : acuses && acuses.length > 0 ? (
          <table className="min-w-full divide-y divide-secondary-200">
            <thead className="bg-secondary-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500">
                  Usuario
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500">
                  Estado
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500">
                  Fecha
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-secondary-200">
              {acuses.map((a) => (
                <tr key={a.id}>
                  <td className="px-4 py-2 text-sm">{a.usuario_nombre}</td>
                  <td className="px-4 py-2">
                    <StatusBadge
                      variant={a.confirmado ? 'success' : 'pending'}
                      label={a.confirmado ? 'Confirmado' : 'Pendiente'}
                    />
                  </td>
                  <td className="px-4 py-2 text-sm">
                    {a.confirmado_at ?? '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-sm text-secondary-500">Sin acuses registrados</p>
        )}
      </Modal>
    </div>
  );
}
