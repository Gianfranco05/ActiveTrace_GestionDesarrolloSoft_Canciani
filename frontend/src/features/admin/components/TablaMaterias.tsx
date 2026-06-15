import { useState } from 'react';

import { MateriaForm } from '@/features/admin/components/MateriaForm';
import { Button } from '@/shared/components/ui/Button';
import { DataTable } from '@/shared/components/ui/DataTable';
import { Input } from '@/shared/components/ui/Input';

import type { Materia, Carrera, CreateMateriaPayload } from '@/features/admin/types/estructura.types';
import type { Column } from '@/shared/components/ui/DataTable';

interface TablaMateriasProps {
  materias: Materia[];
  carreras: Carrera[];
  isLoading: boolean;
  onSave: (data: CreateMateriaPayload, id?: string) => void;
  onToggleEstado: (id: string) => void;
  isSaving: boolean;
}

export function TablaMaterias({ materias, carreras, isLoading, onSave, onToggleEstado, isSaving }: TablaMateriasProps) {
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState<Materia | null>(null);
  const [busqueda, setBusqueda] = useState('');

  const filtered = busqueda
    ? materias.filter((m) => m.nombre.toLowerCase().includes(busqueda.toLowerCase()) || m.codigo.toLowerCase().includes(busqueda.toLowerCase()))
    : materias;

  const columns: Column[] = [
    { key: 'nombre', header: 'Nombre' },
    { key: 'codigo', header: 'Código' },
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
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => { setEditItem(item as Materia); setShowForm(true); }}>
            Editar
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onToggleEstado(item.id as string)}>
            {item.activa ? 'Desactivar' : 'Activar'}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-secondary-900">Materias</h3>
        <div className="flex items-center gap-3">
          <div className="w-64">
            <Input
              label=""
              placeholder="Buscar por nombre o código..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
          </div>
          <Button variant="primary" size="sm" onClick={() => { setShowForm(!showForm); setEditItem(null); }}>
            {showForm ? 'Cancelar' : 'Nueva Materia'}
          </Button>
        </div>
      </div>

      {showForm && (
        <div className="rounded-lg border border-secondary-200 p-4">
          <MateriaForm
            onSubmit={(data) => {
              onSave(data, editItem?.id);
              setShowForm(false);
              setEditItem(null);
            }}
            isSubmitting={isSaving}
            initialData={editItem ? { nombre: editItem.nombre, codigo: editItem.codigo } : undefined}
            carreras={carreras}
          />
        </div>
      )}

      <DataTable
        columns={columns}
        data={filtered}
        keyExtractor={(item) => item.id as string}
        isLoading={isLoading}
        emptyMessage="No hay materias registradas"
      />
    </div>
  );
}
