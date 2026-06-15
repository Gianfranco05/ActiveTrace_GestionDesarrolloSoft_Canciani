import { useState } from 'react';

import { CohorteForm } from '@/features/admin/components/CohorteForm';
import { Button } from '@/shared/components/ui/Button';
import { DataTable } from '@/shared/components/ui/DataTable';
import { Select } from '@/shared/components/ui/Select';

import type { Carrera, CreateCohortePayload } from '@/features/admin/types/estructura.types';
import type { Column } from '@/shared/components/ui/DataTable';

interface TablaCohortesProps {
  cohortes: any[];
  carreras: Carrera[];
  isLoading: boolean;
  onSave: (data: CreateCohortePayload) => void;
  onToggleEstado: (id: string) => void;
  isSaving: boolean;
  selectedCarreraId: string;
  onCarreraChange: (id: string) => void;
}

export function TablaCohortes({
  cohortes,
  carreras,
  isLoading,
  onSave,
  onToggleEstado,
  isSaving,
  selectedCarreraId,
  onCarreraChange,
}: TablaCohortesProps) {
  const [showForm, setShowForm] = useState(false);

  const columns: Column[] = [
    { key: 'nombre', header: 'Nombre' },
    { key: 'anio', header: 'Año inicio' },
    { key: 'vig_desde', header: 'Desde' },
    {
      key: 'vig_hasta', header: 'Hasta',
      render: (item) => (item.vig_hasta as string | null) ?? '—',
    },
    {
      key: 'estado', header: 'Estado',
      render: (item) => (
        <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
          item.activa ? 'bg-green-100 text-green-700' : 'bg-secondary-100 text-secondary-500'
        }`}>
          {item.activa ? 'Activa' : 'Inactiva'}
        </span>
      ),
    },
    {
      key: 'acciones', header: 'Acciones',
      render: (item) => (
        <Button variant="ghost" size="sm" onClick={() => onToggleEstado(item.id as string)}>
          {item.activa ? 'Desactivar' : 'Activar'}
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-secondary-900">Cohortes</h3>
        <div className="flex items-center gap-3">
          <div className="w-64">
            <Select
              label="Filtrar por carrera"
              options={carreras.map((c) => ({ value: c.id, label: `${c.codigo} - ${c.nombre}` }))}
              placeholder="Seleccionar carrera"
              value={selectedCarreraId}
              onChange={(e) => onCarreraChange(e.target.value)}
            />
          </div>
          <div className="pt-5">
            <Button variant="primary" size="sm" onClick={() => setShowForm(!showForm)} disabled={!selectedCarreraId}>
              {showForm ? 'Cancelar' : 'Nueva Cohorte'}
            </Button>
          </div>
        </div>
      </div>

      {showForm && selectedCarreraId && (
        <div className="rounded-lg border border-secondary-200 p-4">
          <CohorteForm
            onSubmit={(data) => {
              onSave(data);
              setShowForm(false);
            }}
            isSubmitting={isSaving}
            carreras={carreras.map((c) => ({ value: c.id, label: `${c.codigo} - ${c.nombre}` }))}
            initialData={{ ...({} as CreateCohortePayload), carrera_id: selectedCarreraId }}
          />
        </div>
      )}

      <DataTable
        columns={columns}
        data={cohortes}
        keyExtractor={(item) => item.id as string}
        isLoading={isLoading}
        emptyMessage={selectedCarreraId ? 'No hay cohortes para esta carrera' : 'Seleccioná una carrera para ver sus cohortes'}
      />
    </div>
  );
}
