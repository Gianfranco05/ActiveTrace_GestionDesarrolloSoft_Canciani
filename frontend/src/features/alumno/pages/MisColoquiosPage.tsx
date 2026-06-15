import { toast } from 'sonner';

import type { Column } from '@/shared/components/ui/DataTable';

import { useMisReservas, useCancelarReserva } from '@/features/alumno/hooks/useAlumno';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { DataTable } from '@/shared/components/ui/DataTable';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';

export function MisColoquiosPage() {
  const { data: reservas, isLoading } = useMisReservas();
  const cancelar = useCancelarReserva();

  const handleCancelar = (reservaId: string) => {
    cancelar.mutate(reservaId, {
      onSuccess: () => toast.success('Reserva cancelada'),
      onError: () => toast.error('No se pudo cancelar la reserva'),
    });
  };

  const columns: Column[] = [
    {
      key: 'evaluacion_id',
      header: 'Convocatoria',
      render: (item: any) => (
        <span className="text-sm text-secondary-600">{item.evaluacion_id ?? '—'}</span>
      ),
    },
    {
      key: 'fecha_hora',
      header: 'Fecha y Hora',
      sortable: true,
      render: (item: any) => (
        <span className="text-sm text-secondary-600">
          {item.fecha_hora
            ? new Date(item.fecha_hora).toLocaleString('es-AR')
            : '—'}
        </span>
      ),
    },
    {
      key: 'estado',
      header: 'Estado',
      sortable: true,
      render: (item: any) => (
        <StatusBadge status={item.estado ?? 'Pendiente'} />
      ),
    },
    {
      key: 'acciones',
      header: '',
      render: (item: any) =>
        item.estado === 'Activa' ? (
          <Button
            variant="danger"
            size="sm"
            isLoading={cancelar.isPending && cancelar.variables === item.id}
            onClick={() => handleCancelar(item.id)}
          >
            Cancelar
          </Button>
        ) : null,
    },
  ];

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Mis Reservas de Coloquio</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Consultá y cancelá tus reservas de coloquios.
        </p>
      </div>

      <Card>
        <DataTable<any>
          columns={columns}
          data={reservas ?? []}
          keyExtractor={(item) => item.id ?? String(Math.random())}
          emptyMessage="No tenés reservas de coloquio todavía"
        />
      </Card>
    </div>
  );
}
