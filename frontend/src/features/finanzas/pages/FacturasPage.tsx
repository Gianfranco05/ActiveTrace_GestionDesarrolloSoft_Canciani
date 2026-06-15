import { useState, useMemo, useCallback } from 'react';
import { toast } from 'sonner';

import { FacturaForm } from '@/features/finanzas/components/FacturaForm';
import { useFacturas, useMutateFactura } from '@/features/finanzas/hooks/useFacturas';
import { Button } from '@/shared/components/ui/Button';
import { DataTable } from '@/shared/components/ui/DataTable';
import { Input } from '@/shared/components/ui/Input';
import { Select } from '@/shared/components/ui/Select';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useFormModal } from '@/shared/hooks/useFormModal';

import type { Factura } from '@/features/finanzas/types/factura.types';
import type { Column } from '@/shared/components/ui/DataTable';

const ESTADOS_FILTER = [
  { value: 'Pendiente', label: 'Pendiente' },
  { value: 'Abonada', label: 'Abonada' },
];

const defaultFormData = new FormData();

export function FacturasPage() {
  const [estadoFilter, setEstadoFilter] = useState('');
  const [busqueda, setBusqueda] = useState('');

  const modal = useFormModal<FormData, Factura>(defaultFormData);

  const filter = useMemo(
    () => ({
      estado: estadoFilter || undefined,
      busqueda: busqueda || undefined,
    }),
    [estadoFilter, busqueda]
  );

  const { data: facturas, isLoading } = useFacturas(filter);
  const mutate = useMutateFactura();

  const handleSubmit = useCallback(
    async (formData: FormData) => {
      try {
        await mutate.create.mutateAsync(formData);
        toast.success('Factura cargada correctamente');
        modal.close();
      } catch {
        toast.error('Error al cargar la factura');
      }
    },
    [modal, mutate.create]
  );

  const columns = useMemo<Column[]>(
    () => [
      { key: 'docente_nombre', header: 'Docente' },
      { key: 'periodo', header: 'Período' },
      { key: 'detalle', header: 'Detalle' },
      {
        key: 'archivo',
        header: 'Archivo',
        render: (item) =>
          `${item.archivo_nombre as string} (${(
            (item.archivo_tamano as number) / 1024
          ).toFixed(0)} KB)`,
      },
      {
        key: 'estado',
        header: 'Estado',
        render: (item) => (
          <span
            className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
              item.estado === 'Abonada'
                ? 'bg-green-100 text-green-700'
                : 'bg-amber-100 text-amber-700'
            }`}
          >
            {item.estado as string}
          </span>
        ),
      },
      { key: 'fecha_carga', header: 'Fecha Carga' },
      {
        key: 'acciones',
        header: 'Acciones',
        render: (item) => (
          <Button
            variant="ghost"
            size="sm"
            onClick={async () => {
              try {
                await mutate.changeEstado.mutateAsync({
                  id: item.id as string,
                  estado:
                    item.estado === 'Pendiente' ? 'Abonada' : 'Pendiente',
                } as { id: string; estado: 'Pendiente' | 'Abonada' });
                toast.success(
                  item.estado === 'Pendiente'
                    ? 'Factura marcada como abonada'
                    : 'Factura revertida a pendiente'
                );
              } catch {
                toast.error('Error al cambiar el estado');
              }
            }}
            isLoading={mutate.changeEstado.isPending}
            aria-label={`Cambiar estado de ${item.docente_nombre as string}`}
          >
            {(item.estado as string) === 'Pendiente'
              ? 'Marcar como abonada'
              : 'Revertir a pendiente'}
          </Button>
        ),
      },
    ],
    [mutate]
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Facturas</h1>
          <p className="mt-1 text-sm text-secondary-500">
            Gestión de facturas de docentes
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => modal.openCreate()}
        >
          {modal.isOpen ? 'Cancelar' : 'Nueva Factura'}
        </Button>
      </div>

      {modal.isOpen && (
        <div className="rounded-lg border border-secondary-200 p-4">
          <FacturaForm
            onSubmit={handleSubmit}
            isSubmitting={mutate.create.isPending}
            docentes={[]}
          />
        </div>
      )}

      <div className="flex flex-wrap gap-4">
        <div className="w-48">
          <Select
            label="Estado"
            options={ESTADOS_FILTER}
            placeholder="Todos"
            value={estadoFilter}
            onChange={(e) => setEstadoFilter(e.target.value)}
          />
        </div>
        <div className="w-64">
          <Input
            label="Buscar"
            placeholder="Docente, detalle..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Spinner size="lg" />
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={facturas ?? []}
          keyExtractor={(item) => item.id as string}
          emptyMessage="No hay facturas registradas"
        />
      )}
    </div>
  );
}
