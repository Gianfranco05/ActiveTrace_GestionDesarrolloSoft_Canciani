import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';

import type { CreateCarreraPayload } from '@/features/admin/types/estructura.types';

const carreraSchema = z.object({
  codigo: z.string().min(1, 'El código es requerido'),
  nombre: z.string().min(1, 'El nombre es requerido'),
});

type CarreraFormData = z.infer<typeof carreraSchema>;

interface CarreraFormProps {
  onSubmit: (data: CreateCarreraPayload) => void;
  isSubmitting: boolean;
  initialData?: CreateCarreraPayload;
}

export function CarreraForm({ onSubmit, isSubmitting, initialData }: CarreraFormProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<CarreraFormData>({
    resolver: zodResolver(carreraSchema),
    defaultValues: initialData ?? { codigo: '', nombre: '' },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Input label="Código" error={errors.codigo?.message} {...register('codigo')} />
      <Input label="Nombre" error={errors.nombre?.message} {...register('nombre')} />
      <Button type="submit" isLoading={isSubmitting}>
        {initialData ? 'Actualizar' : 'Crear'} Carrera
      </Button>
    </form>
  );
}
