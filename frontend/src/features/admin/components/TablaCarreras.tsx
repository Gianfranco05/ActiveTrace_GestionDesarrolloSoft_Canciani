import { useState } from 'react';

import { CarreraForm } from '@/features/admin/components/CarreraForm';
import { Button } from '@/shared/components/ui/Button';
import { DataTable } from '@/shared/components/ui/DataTable';

import type { Carrera, CreateCarreraPayload } from '@/features/admin/types/estructura.types';
import type { Column } from '@/shared/components/ui/DataTable';

interface TablaCarrerasProps {
  carreras: Carrera[];
  isLoading: boolean;
  onSave: (data: CreateCarreraPayload) => void;
  onToggleEstado: (id: string) => void;
  isSaving: boolean;
}

export function TablaCarreras({ carreras, isLoading, onSave, onToggleEstado, isSaving }: TablaCarrerasProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const columns: Column[] = [
    { key: 'codigo', header: 'Código' },
    { key: 'nombre', header: 'Nombre' },
    {
      key: 'estado',
      header: 'Estado',
      render: (item) => (
        <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
          item.activa ? 'bg-green-100 text-green-700' : 'bg-secondary-100 text-secondary-500'
        }`}>
          {item.activa ? 'Activa' : 'Inactiva'}
        </span>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      render: (item) => (
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setEditingId(item.id as string);
              setShowForm(true);
            }}
          >
            Editar
          </Button>
          <Button
            variant={item.activa ? 'ghost' : 'danger'}
            size="sm"
            onClick={() => onToggleEstado(item.id as string)}
          >
            {item.activa ? 'Desactivar' : 'Activar'}
          </Button>
        </div>
      ),
    },
  ];

  const editingCarrera = editingId ? carreras.find((c) => c.id === editingId) : undefined;
  const initialData = editingCarrera ? { codigo: editingCarrera.codigo, nombre: editingCarrera.nombre } : undefined;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-secondary-900">Carreras</h3>
        <Button variant="primary" size="sm" onClick={() => { setEditingId(null); setShowForm(!showForm); }}>
          {showForm ? 'Cancelar' : 'Nueva Carrera'}
        </Button>
      </div>

      {showForm && (
        <div className="rounded-lg border border-secondary-200 p-4">
          <CarreraForm
            key={editingId ?? 'new'}
            onSubmit={(data) => {
              onSave(data);
              setShowForm(false);
              setEditingId(null);
            }}
            isSubmitting={isSaving}
            initialData={initialData}
          />
        </div>
      )}

      <DataTable
        columns={columns}
        data={carreras}
        keyExtractor={(item) => item.id as string}
        isLoading={isLoading}
        emptyMessage="No hay carreras registradas"
      />
    </div>
  );
}
