import { zodResolver } from '@hookform/resolvers/zod';
import { useForm, type Resolver } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';

import type { CreateUsuarioPayload } from '@/features/admin/types/usuario.types';

const ROLES_OPTIONS = [
  'ADMIN',
  'COORDINADOR',
  'PROFESOR',
  'TUTOR',
  'NEXO',
  'FINANZAS',
  'ALUMNO',
] as const;

const usuarioCreateSchema = z.object({
  nombre: z.string().min(1, 'El nombre es requerido'),
  email: z.string().email('Email inválido'),
  password: z.string().min(1, 'La contraseña es requerida'),
  roles: z.array(z.string()).min(1, 'Al menos un rol es requerido'),
  cbu: z.string().optional(),
  banco: z.string().optional(),
  titular: z.string().optional(),
});

const usuarioEditSchema = z.object({
  nombre: z.string().min(1, 'El nombre es requerido'),
  email: z.string().email('Email inválido'),
  password: z.string().optional(),
  roles: z.array(z.string()).min(1, 'Al menos un rol es requerido'),
  cbu: z.string().optional(),
  banco: z.string().optional(),
  titular: z.string().optional(),
});

interface UsuarioFormData {
  nombre: string;
  email: string;
  password: string;
  roles: string[];
  cbu?: string;
  banco?: string;
  titular?: string;
}

interface UsuarioFormProps {
  onSubmit: (data: CreateUsuarioPayload) => void;
  isSubmitting: boolean;
  initialData?: CreateUsuarioPayload;
}

export function UsuarioForm({ onSubmit, isSubmitting, initialData }: UsuarioFormProps) {
  const isEditing = !!initialData;
  const schema = isEditing ? usuarioEditSchema : usuarioCreateSchema;
  const { register, handleSubmit, formState: { errors } } = useForm<UsuarioFormData>({
    resolver: zodResolver(schema) as Resolver<UsuarioFormData>,
    defaultValues: initialData
      ? { nombre: initialData.nombre, email: initialData.email, password: '', roles: initialData.roles, cbu: initialData.datos_bancarios?.cbu ?? '', banco: initialData.datos_bancarios?.banco ?? '', titular: initialData.datos_bancarios?.titular ?? '' }
      : { nombre: '', email: '', password: '', roles: [], cbu: '', banco: '', titular: '' },
  });

  const handleFormSubmit = (data: UsuarioFormData) => {
    const payload: CreateUsuarioPayload = {
      nombre: data.nombre,
      email: data.email,
      password: data.password,
      roles: data.roles,
      datos_bancarios: data.cbu ? { cbu: data.cbu, banco: data.banco ?? '', titular: data.titular ?? '' } : null,
    };
    onSubmit(payload);
  };

  return (
    <Card className="border-primary-200 bg-primary-50/50">
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input label="Nombre" error={errors.nombre?.message} {...register('nombre')} />
          <Input label="Email" type="email" error={errors.email?.message} {...register('email')} />
        </div>
        <Input
          label={isEditing ? 'Nueva contraseña (dejar vacía para no cambiar)' : 'Contraseña'}
          type="password"
          error={errors.password?.message}
          {...register('password')}
        />

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-secondary-700">Roles</legend>
          <div className="flex flex-wrap gap-3">
            {ROLES_OPTIONS.map((role) => (
              <label
                key={role}
                className={`inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition-colors ${
                  'border-secondary-200 bg-white text-secondary-600 hover:border-secondary-400'
                }`}
              >
                <input
                  type="checkbox"
                  value={role}
                  {...register('roles')}
                  className="rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
                />
                {role}
              </label>
            ))}
          </div>
          {errors.roles && <p className="mt-1 text-sm text-danger-600">{errors.roles.message}</p>}
        </fieldset>

        <details className="rounded-lg border border-secondary-200 p-3">
          <summary className="cursor-pointer text-sm font-medium text-secondary-700">
            Datos bancarios (opcional)
          </summary>
          <div className="mt-3 space-y-3">
            <Input label="CBU" {...register('cbu')} />
            <Input label="Banco" {...register('banco')} />
            <Input label="Titular" {...register('titular')} />
          </div>
        </details>

        <Button type="submit" isLoading={isSubmitting}>
          {initialData ? 'Actualizar' : 'Crear'} Usuario
        </Button>
      </form>
    </Card>
  );
}
