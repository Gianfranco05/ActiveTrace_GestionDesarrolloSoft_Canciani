import { zodResolver } from '@hookform/resolvers/zod';
import { useForm, type Resolver } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';

import type { CreateCohortePayload } from '@/features/admin/types/estructura.types';

const cohorteSchema = z.object({
  carrera_id: z.string().min(1, 'La carrera es requerida'),
  nombre: z.string().min(1, 'El nombre es requerido'),
  anio: z.coerce.number().int().positive('El año debe ser positivo'),
  vig_desde: z.string().min(1, 'La fecha desde es requerida'),
  vig_hasta: z.string().nullable().optional(),
});

interface CohorteFormData {
  carrera_id: string;
  nombre: string;
  anio: number;
  vig_desde: string;
  vig_hasta?: string | null;
}

interface CohorteFormProps {
  onSubmit: (data: CreateCohortePayload) => void;
  isSubmitting: boolean;
  carreras: { value: string; label: string }[];
  initialData?: CreateCohortePayload;
}

export function CohorteForm({ onSubmit, isSubmitting, carreras, initialData }: CohorteFormProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<CohorteFormData>({
    resolver: zodResolver(cohorteSchema) as Resolver<CohorteFormData>,
    defaultValues: initialData ?? { carrera_id: '', nombre: '', anio: new Date().getFullYear(), vig_desde: '', vig_hasta: null },
  });

  return (
    <form onSubmit={handleSubmit((data) => onSubmit(data))} className="space-y-4">
      <div className="w-full">
        <label className="mb-1 block text-sm font-medium text-secondary-700">Carrera</label>
        <select
          {...register('carrera_id')}
          className="block w-full rounded-lg border border-secondary-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1"
        >
          <option value="">Seleccionar carrera</option>
          {carreras.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
        {errors.carrera_id && <p className="mt-1 text-sm text-danger-600">{errors.carrera_id.message}</p>}
      </div>
      <Input label="Nombre" error={errors.nombre?.message} {...register('nombre')} />
      <Input label="Año de inicio" type="number" error={errors.anio?.message} {...register('anio')} />
      <Input label="Vigencia desde" type="date" error={errors.vig_desde?.message} {...register('vig_desde')} />
      <Input label="Vigencia hasta (opcional)" type="date" {...register('vig_hasta')} />
      <Button type="submit" isLoading={isSubmitting}>
        {initialData ? 'Actualizar' : 'Crear'} Cohorte
      </Button>
    </form>
  );
}
