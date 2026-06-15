import { zodResolver } from '@hookform/resolvers/zod';
import { useForm, type Resolver } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';

import type { CreateSalarioBasePayload } from '@/features/finanzas/types/salario.types';

const salarioBaseSchema = z.object({
  rol: z.string().min(1, 'El rol es requerido'),
  monto: z.coerce.number().positive('El monto debe ser positivo'),
  desde: z.string().min(1, 'La fecha desde es requerida'),
  hasta: z.string().nullable().optional(),
});

interface SalarioBaseFormData {
  rol: string;
  monto: number;
  desde: string;
  hasta?: string | null;
}

interface SalarioBaseFormProps {
  onSubmit: (data: CreateSalarioBasePayload) => void;
  isSubmitting: boolean;
  initialData?: CreateSalarioBasePayload;
}

export function SalarioBaseForm({ onSubmit, isSubmitting, initialData }: SalarioBaseFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SalarioBaseFormData>({
    resolver: zodResolver(salarioBaseSchema) as Resolver<SalarioBaseFormData>,
    defaultValues: initialData ?? { rol: '', monto: 0, desde: '', hasta: null },
  });

  return (
    <form onSubmit={handleSubmit((data) => onSubmit(data))} className="space-y-4">
      <Input label="Rol" error={errors.rol?.message} {...register('rol')} />
      <Input label="Monto" type="number" step="0.01" error={errors.monto?.message} {...register('monto')} />
      <Input label="Desde" type="date" error={errors.desde?.message} {...register('desde')} />
      <Input label="Hasta (opcional)" type="date" {...register('hasta')} />
      <Button type="submit" isLoading={isSubmitting}>
        {initialData ? 'Actualizar' : 'Crear'} Salario Base
      </Button>
    </form>
  );
}
