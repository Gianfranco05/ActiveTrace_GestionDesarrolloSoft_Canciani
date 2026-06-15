import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { useColoquioMetricas, useConvocatorias, useImportarAlumnos } from '@/features/coordinacion/coloquios/hooks/useColoquios';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { FileUpload } from '@/shared/components/ui/FileUpload';
import { Modal } from '@/shared/components/ui/Modal';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';

import type { Convocatoria } from '@/features/coordinacion/coloquios/types/coloquios.types';

export function ColoquiosPage() {
  const { data: metricas, isLoading: loadingMetricas } = useColoquioMetricas();
  const { data: convocatorias, isLoading: loadingConv } = useConvocatorias();
  const { mutateAsync: importar, isPending: importing } = useImportarAlumnos();
  const [importModal, setImportModal] = useState<Convocatoria | null>(null);

  const columns = useMemo<Column[]>(
    () => [
      { key: 'materia_nombre', header: 'Materia' },
      { key: 'instancia', header: 'Instancia' },
      {
        key: 'cupos_por_dia',
        header: 'Días',
        render: (item: any) => <span>{item.cupos_por_dia?.length ?? 0}</span>,
      },
      { key: 'total_convocados', header: 'Convocados' },
      { key: 'reservas_activas', header: 'Reservas' },
      { key: 'cupos_libres', header: 'Cupos Libres' },
      {
        key: 'activa',
        header: 'Estado',
        render: (item) => <StatusBadge variant={item.activa ? 'active' : 'inactive'} label={item.activa ? 'Activa' : 'Inactiva'} />,
      },
      {
        key: 'acciones',
        header: 'Acciones',
        render: (item) => (
          <div className="flex gap-2">
            <Button size="sm" variant="ghost" aria-label="Importar alumnos" onClick={(e) => { e.stopPropagation(); setImportModal(item); }}>Importar</Button>
            <Link to={`/coordinacion/coloquios/${item.id}/reservas`}>
              <Button size="sm" variant="ghost" aria-label="Ver reservas">Reservas</Button>
            </Link>
          </div>
        ),
      },
    ],
    []
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-secondary-900">Coloquios</h1>
        <div className="flex gap-2">
          <Link to="/coordinacion/coloquios/registro">
            <Button variant="secondary" size="sm">Registro Académico</Button>
          </Link>
          <Link to="/coordinacion/coloquios/nueva">
            <Button variant="primary" size="sm">Nueva Convocatoria</Button>
          </Link>
        </div>
      </div>

      {loadingMetricas ? (
        <div className="flex justify-center py-8"><Spinner /></div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <Card>
            <div className="text-center">
              <p className="text-2xl font-bold">{metricas?.total_alumnos ?? 0}</p>
              <p className="text-sm text-secondary-500">Alumnos</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-2xl font-bold">{metricas?.instancias_activas ?? 0}</p>
              <p className="text-sm text-secondary-500">Instancias Activas</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-2xl font-bold">{metricas?.reservas_activas ?? 0}</p>
              <p className="text-sm text-secondary-500">Reservas Activas</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-2xl font-bold">{metricas?.notas_registradas ?? 0}</p>
              <p className="text-sm text-secondary-500">Notas Registradas</p>
            </div>
          </Card>
        </div>
      )}

      {loadingConv ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : (
        <Card header={<h3 className="font-semibold">Convocatorias</h3>}>
          <DataTable columns={columns} data={convocatorias ?? []} keyExtractor={(c) => c.id} />
        </Card>
      )}

      <Modal isOpen={!!importModal} onClose={() => setImportModal(null)} title="Importar Alumnos">
        <FileUpload
          accept=".csv,.xlsx"
          onFileSelect={async (file) => {
            if (importModal) {
              await importar({ convocatoriaId: importModal.id, archivo: file });
              setImportModal(null);
            }
          }}
          isLoading={importing}
          label="Subir archivo de alumnos"
        />
      </Modal>
    </div>
  );
}
