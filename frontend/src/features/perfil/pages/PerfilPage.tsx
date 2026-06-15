import { useState } from 'react';
import { toast } from 'sonner';

import { usePerfil, useUpdatePerfil } from '@/features/perfil/hooks/usePerfil';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Spinner } from '@/shared/components/ui/Spinner';

import type { PerfilUpdateRequest } from '../types/perfil.types';

export function PerfilPage() {
  const { data: perfil, isLoading } = usePerfil();
  const updatePerfil = useUpdatePerfil();

  const [form, setForm] = useState<PerfilUpdateRequest>({});
  const [initialized, setInitialized] = useState(false);

  if (perfil && !initialized) {
    setForm({
      nombre: perfil.nombre,
      apellidos: perfil.apellidos,
      dni: perfil.dni,
      banco: perfil.banco,
      cbu: perfil.cbu,
      alias_cbu: perfil.alias_cbu,
      regional: perfil.regional,
      legajo_profesional: perfil.legajo_profesional,
      facturador: perfil.facturador,
    });
    setInitialized(true);
  }

  const handleChange = (field: keyof PerfilUpdateRequest) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm((prev) => ({ ...prev, [field]: value || null }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const cleaned: PerfilUpdateRequest = {};
    for (const [key, value] of Object.entries(form)) {
      if (value !== undefined && value !== '') {
        (cleaned as Record<string, unknown>)[key] = value;
      }
    }

    updatePerfil.mutate(cleaned, {
      onSuccess: () => toast.success('Perfil actualizado correctamente'),
      onError: () => toast.error('No se pudo actualizar el perfil'),
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!perfil) {
    return (
      <div className="py-4">
        <Card>
          <p className="text-center text-sm text-secondary-500">
            No se pudo cargar la información del perfil.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Mi Perfil</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Consultá y editá tus datos personales.
        </p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Nombre"
              value={form.nombre ?? ''}
              onChange={handleChange('nombre')}
            />
            <Input
              label="Apellidos"
              value={form.apellidos ?? ''}
              onChange={handleChange('apellidos')}
            />
          </div>

          <div>
            <Input label="Email" value={perfil.email} disabled />
            <p className="mt-1 text-xs text-secondary-400">
              El email no se puede modificar.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="DNI"
              value={form.dni ?? ''}
              onChange={handleChange('dni')}
            />
            <Input
              label="Legajo Profesional"
              value={form.legajo_profesional ?? ''}
              onChange={handleChange('legajo_profesional')}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Regional"
              value={form.regional ?? ''}
              onChange={handleChange('regional')}
            />
            <Input
              label="Banco"
              value={form.banco ?? ''}
              onChange={handleChange('banco')}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="CBU"
              value={form.cbu ?? ''}
              onChange={handleChange('cbu')}
            />
            <Input
              label="Alias CBU"
              value={form.alias_cbu ?? ''}
              onChange={handleChange('alias_cbu')}
            />
          </div>

          <label className="flex items-center gap-2 text-sm text-secondary-700">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
              checked={form.facturador ?? false}
              onChange={handleChange('facturador')}
            />
            Facturador
          </label>

          <div className="border-t border-secondary-200 pt-4">
            <p className="text-xs text-secondary-400">
              Legajo interno: {perfil.legajo ?? '—'} &middot; CUIL: {perfil.cuil ?? '—'} &middot; Estado: {perfil.estado}
            </p>
          </div>

          <div className="flex justify-end">
            <Button
              type="submit"
              isLoading={updatePerfil.isPending}
              disabled={updatePerfil.isPending}
            >
              Guardar cambios
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
