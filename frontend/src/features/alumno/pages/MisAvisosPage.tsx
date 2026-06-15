import { useState } from 'react';
import { toast } from 'sonner';

import type { Column } from '@/shared/components/ui/DataTable';
import type { AvisoAlumno } from '@/features/alumno/types/alumno.types';

import { useMisAvisos, useConfirmarAviso } from '@/features/alumno/hooks/useAlumno';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { DataTable } from '@/shared/components/ui/DataTable';
import { Pagination } from '@/shared/components/ui/Pagination';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';

const PAGE_SIZE = 20;

export function MisAvisosPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useMisAvisos(page);
  const confirmar = useConfirmarAviso();

  const handleConfirmar = (avisoId: string) => {
    confirmar.mutate(avisoId, {
      onSuccess: () => toast.success('Aviso confirmado'),
      onError: () => toast.error('No se pudo confirmar el aviso'),
    });
  };

  const columns: Column[] = [
    {
      key: 'titulo',
      header: 'Título',
      sortable: true,
      render: (item: AvisoAlumno) => (
        <p className="font-medium text-secondary-900">{item.titulo}</p>
      ),
    },
    {
      key: 'created_at',
      header: 'Fecha',
      sortable: true,
      render: (item: AvisoAlumno) => (
        <span className="text-sm text-secondary-600">
          {new Date(item.created_at).toLocaleDateString('es-AR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
          })}
        </span>
      ),
    },
    {
      key: 'estado',
      header: 'Estado',
      sortable: true,
      render: (item: AvisoAlumno) => (
        <StatusBadge
          status={item.acknowledged ? 'Confirmado' : 'Pendiente'}
        />
      ),
    },
    {
      key: 'acciones',
      header: '',
      render: (item: AvisoAlumno) =>
        !item.acknowledged ? (
          <Button
            variant="ghost"
            size="sm"
            isLoading={confirmar.isPending && confirmar.variables === item.id}
            onClick={() => handleConfirmar(item.id)}
          >
            Confirmar
          </Button>
        ) : null,
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Mis Avisos</h1>
          <p className="mt-1 text-sm text-secondary-500">
            Avisos publicados por tu coordinación.
          </p>
        </div>
        <Card>
          <p className="text-sm text-secondary-500 text-center py-4">
            No se pudieron cargar los avisos. Intentá de nuevo más tarde.
          </p>
        </Card>
      </div>
    );
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Mis Avisos</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Avisos publicados por tu coordinación.
        </p>
      </div>

      <Card padding={false}>
        <div className="px-6 pt-4">
          <DataTable<AvisoAlumno>
            columns={columns}
            data={items}
            keyExtractor={(item) => item.id}
            emptyMessage="No tenés avisos todavía"
          />
        </div>
        {totalPages > 1 && (
          <div className="px-6 py-3">
            <Pagination
              page={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          </div>
        )}
      </Card>
    </div>
  );
}
