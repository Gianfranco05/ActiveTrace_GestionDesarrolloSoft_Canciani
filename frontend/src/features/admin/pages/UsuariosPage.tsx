import { useState, useMemo, useCallback } from 'react';
import { toast } from 'sonner';

import { FiltrosUsuario } from '@/features/admin/components/FiltrosUsuario';
import { UsuarioForm } from '@/features/admin/components/UsuarioForm';
import { useUsuarios, useMutateUsuario } from '@/features/admin/hooks/useUsuarios';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { ConfirmDialog } from '@/shared/components/ui/ConfirmDialog';
import { DataTable } from '@/shared/components/ui/DataTable';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useConfirmDialog } from '@/shared/hooks/useConfirmDialog';
import { useFormModal } from '@/shared/hooks/useFormModal';

import type { Usuario, CreateUsuarioPayload } from '@/features/admin/types/usuario.types';
import type { Column } from '@/shared/components/ui/DataTable';

const defaultFormData: CreateUsuarioPayload = {
  nombre: '',
  email: '',
  roles: [],
  datos_bancarios: null,
};

export function UsuariosPage() {
  const [rolFilter, setRolFilter] = useState('');
  const [activoFilter, setActivoFilter] = useState('');
  const [busqueda, setBusqueda] = useState('');

  const modal = useFormModal<CreateUsuarioPayload, Usuario>(defaultFormData);
  const toggleDialog = useConfirmDialog<Usuario>();

  const filter = useMemo(
    () => ({
      rol: rolFilter || undefined,
      activo: activoFilter ? activoFilter === 'true' : undefined,
      busqueda: busqueda || undefined,
    }),
    [rolFilter, activoFilter, busqueda]
  );

  const { data: usuarios, isLoading } = useUsuarios(filter);
  const mutate = useMutateUsuario();

  const handleToggleEstado = useCallback(async () => {
    if (!toggleDialog.item) return;
    try {
      await mutate.toggleEstado.mutateAsync(toggleDialog.item.id);
      toast.success(
        toggleDialog.item.activo
          ? 'Usuario desactivado'
          : 'Usuario activado'
      );
      toggleDialog.close();
    } catch {
      toast.error('Error al cambiar estado');
    }
  }, [toggleDialog, mutate.toggleEstado]);

  const handleSubmit = useCallback(
    async (data: CreateUsuarioPayload) => {
      try {
        if (modal.selectedItem) {
          await mutate.update.mutateAsync({ id: modal.selectedItem.id, payload: data });
          toast.success('Usuario actualizado');
        } else {
          await mutate.create.mutateAsync(data);
          toast.success('Usuario creado');
        }
        modal.close();
      } catch {
        toast.error('Error al guardar usuario');
      }
    },
    [modal, mutate]
  );

  const openEdit = useCallback(
    (item: Usuario) => {
      const initialData: CreateUsuarioPayload = {
        nombre: item.nombre,
        email: item.email,
        roles: item.roles,
        datos_bancarios: item.datos_bancarios ?? null,
      };
      modal.openEdit(item, initialData);
    },
    [modal]
  );

  const columns = useMemo<Column[]>(
    () => [
      { key: 'nombre', header: 'Nombre' },
      { key: 'email', header: 'Email' },
      {
        key: 'roles',
        header: 'Roles',
        render: (item) => ((item.roles as string[] | undefined) ?? []).join(', ') || '—',
      },
      {
        key: 'activo',
        header: 'Estado',
        render: (item) => (
          <span
            className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
              item.activo
                ? 'bg-green-100 text-green-700'
                : 'bg-secondary-100 text-secondary-500'
            }`}
          >
            {item.activo ? 'Activo' : 'Inactivo'}
          </span>
        ),
      },
      {
        key: 'ultimo_acceso',
        header: 'Último Acceso',
        render: (item) => (item.ultimo_acceso as string | null) ?? '—',
      },
      {
        key: 'acciones',
        header: 'Acciones',
        render: (item) => (
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => openEdit(item as Usuario)}
              aria-label={`Editar ${(item as Usuario).nombre}`}
            >
              Editar
            </Button>
            <Button
              variant={(item as Usuario).activo ? 'ghost' : 'danger'}
              size="sm"
              onClick={() => toggleDialog.open(item as Usuario)}
              aria-label={`${(item as Usuario).activo ? 'Desactivar' : 'Activar'} ${(item as Usuario).nombre}`}
            >
              {(item as Usuario).activo ? 'Desactivar' : 'Activar'}
            </Button>
          </div>
        ),
      },
    ],
    [openEdit, toggleDialog]
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Usuarios</h1>
          <p className="mt-1 text-sm text-secondary-500">
            Gestión de usuarios del tenant
          </p>
        </div>
        <Button
          variant={modal.isOpen && !modal.selectedItem ? 'secondary' : 'primary'}
          size="sm"
          onClick={() => modal.isOpen && !modal.selectedItem ? modal.close() : modal.openCreate()}
        >
          {modal.isOpen && !modal.selectedItem ? 'Cancelar' : 'Nuevo Usuario'}
        </Button>
      </div>

      <FiltrosUsuario
        rol={rolFilter}
        activo={activoFilter}
        busqueda={busqueda}
        onRolChange={setRolFilter}
        onActivoChange={setActivoFilter}
        onBusquedaChange={setBusqueda}
      />

      {modal.isOpen && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-primary-600">
            {modal.selectedItem ? 'Editar usuario' : 'Nuevo usuario'}
          </h3>
          <UsuarioForm
            key={modal.selectedItem?.id ?? 'new'}
            onSubmit={handleSubmit}
            isSubmitting={mutate.create.isPending || mutate.update.isPending}
            initialData={
              modal.selectedItem
                ? {
                    nombre: modal.selectedItem.nombre,
                    email: modal.selectedItem.email,
                    roles: modal.selectedItem.roles,
                    datos_bancarios: modal.selectedItem.datos_bancarios,
                  }
                : undefined
            }
          />
        </div>
      )}

      <Card>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-secondary-500">Listado de usuarios</h3>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <Spinner size="lg" />
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={usuarios ?? []}
            keyExtractor={(item) => item.id as string}
            emptyMessage="No hay usuarios registrados"
          />
        )}
      </Card>

      <ConfirmDialog
        isOpen={toggleDialog.isOpen}
        title="Cambiar Estado"
        message={
          <span>
            ¿Estás seguro de{' '}
            {toggleDialog.item?.activo ? 'desactivar' : 'activar'} al usuario "
            <strong>{toggleDialog.item?.nombre}</strong>"?
          </span>
        }
        confirmLabel={toggleDialog.item?.activo ? 'Desactivar' : 'Activar'}
        variant={toggleDialog.item?.activo ? 'danger' : 'primary'}
        onConfirm={handleToggleEstado}
        onCancel={toggleDialog.close}
      />
    </div>
  );
}
