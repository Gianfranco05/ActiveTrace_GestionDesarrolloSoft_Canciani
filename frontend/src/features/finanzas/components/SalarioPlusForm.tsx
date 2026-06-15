import { zodResolver } from '@hookform/resolvers/zod';
import { useForm, type Resolver } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';

import type { CreateSalarioPlusPayload } from '@/features/finanzas/types/salario.types';

const salarioPlusSchema = z.object({
  grupo: z.string().min(1, 'El grupo es requerido'),
  rol: z.string().min(1, 'El rol es requerido'),
  descripcion: z.string().min(1, 'La descripción es requerida'),
  monto: z.coerce.number().positive('El monto debe ser positivo'),
  desde: z.string().min(1, 'La fecha desde es requerida'),
  hasta: z.string().nullable().optional(),
});

interface SalarioPlusFormData {
  grupo: string;
  rol: string;
  descripcion: string;
  monto: number;
  desde: string;
  hasta?: string | null;
}

interface SalarioPlusFormProps {
  onSubmit: (data: CreateSalarioPlusPayload) => void;
  isSubmitting: boolean;
  initialData?: CreateSalarioPlusPayload;
}

export function SalarioPlusForm({ onSubmit, isSubmitting, initialData }: SalarioPlusFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SalarioPlusFormData>({
    resolver: zodResolver(salarioPlusSchema) as Resolver<SalarioPlusFormData>,
    defaultValues: initialData ?? { grupo: '', rol: '', descripcion: '', monto: 0, desde: '', hasta: null },
  });

  return (
    <form onSubmit={handleSubmit((data) => onSubmit(data))} className="space-y-4">
      <Input label="Grupo" error={errors.grupo?.message} {...register('grupo')} />
      <Input label="Rol" error={errors.rol?.message} {...register('rol')} />
      <Input label="Descripción" error={errors.descripcion?.message} {...register('descripcion')} />
      <Input label="Monto" type="number" step="0.01" error={errors.monto?.message} {...register('monto')} />
      <Input label="Desde" type="date" error={errors.desde?.message} {...register('desde')} />
      <Input label="Hasta (opcional)" type="date" {...register('hasta')} />
      <Button type="submit" isLoading={isSubmitting}>
        {initialData ? 'Actualizar' : 'Crear'} Salario Plus
      </Button>
    </form>
  );
}
