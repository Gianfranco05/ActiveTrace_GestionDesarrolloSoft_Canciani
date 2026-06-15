import { zodResolver } from '@hookform/resolvers/zod';
import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';

import type { CreateMateriaPayload } from '@/features/admin/types/estructura.types';

const materiaSchema = z.object({
  nombre: z.string().min(1, 'El nombre es requerido'),
  codigo: z.string().min(1, 'El código es requerido'),
  carrera_ids: z.array(z.string()).default([]),
});

type MateriaFormData = z.infer<typeof materiaSchema>;

interface MateriaFormProps {
  onSubmit: (data: CreateMateriaPayload) => void;
  isSubmitting: boolean;
  initialData?: CreateMateriaPayload;
  carreras: { id: string; codigo: string; nombre: string }[];
}

export function MateriaForm({ onSubmit, isSubmitting, initialData, carreras }: MateriaFormProps) {
  const { register, handleSubmit, control, formState: { errors } } = useForm<MateriaFormData>({
    resolver: zodResolver(materiaSchema) as any,
    defaultValues: {
      nombre: initialData?.nombre ?? '',
      codigo: initialData?.codigo ?? '',
      carrera_ids: initialData?.carrera_ids ?? [],
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit as any)} className="space-y-4">
      <Input label="Nombre" error={errors.nombre?.message} {...register('nombre')} />
      <Input label="Código" error={errors.codigo?.message} {...register('codigo')} />

      {carreras.length > 0 && (
        <fieldset>
          <legend className="mb-2 text-sm font-medium text-secondary-700">Carreras</legend>
          <Controller
            name="carrera_ids"
            control={control}
            render={({ field }) => (
              <div className="flex flex-wrap gap-3">
                {carreras.map((c) => {
                  const checked = field.value.includes(c.id);
                  return (
                    <label
                      key={c.id}
                      className={`inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition-colors ${
                        checked
                          ? 'border-primary-500 bg-primary-50 text-primary-800'
                          : 'border-secondary-200 bg-white text-secondary-600 hover:border-secondary-400'
                      }`}
                    >
                      <input
                        type="checkbox"
                        className="sr-only"
                        checked={checked}
                        onChange={() => {
                          if (checked) {
                            field.onChange(field.value.filter((id: string) => id !== c.id));
                          } else {
                            field.onChange([...field.value, c.id]);
                          }
                        }}
                      />
                      {c.codigo} — {c.nombre}
                    </label>
                  );
                })}
              </div>
            )}
          />
        </fieldset>
      )}

      <Button type="submit" isLoading={isSubmitting}>
        {initialData ? 'Actualizar' : 'Crear'} Materia
      </Button>
    </form>
  );
}
