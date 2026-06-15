import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { FacturaFileInput } from '@/features/finanzas/components/FacturaFileInput';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ACCEPTED_FILE_TYPES = ['application/pdf'];

const facturaSchema = z.object({
  docente_id: z.string().min(1, 'El docente es requerido'),
  periodo: z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/, 'Formato AAAA-MM requerido'),
  detalle: z.string().min(1, 'El detalle es requerido'),
  archivo: z
    .instanceof(File)
    .refine((f) => f.size > 0, 'El archivo es requerido')
    .refine((f) => f.size <= MAX_FILE_SIZE, 'El archivo no puede superar 10 MB')
    .refine((f) => ACCEPTED_FILE_TYPES.includes(f.type), 'Solo se permiten archivos PDF'),
});

type FacturaFormData = z.infer<typeof facturaSchema>;

interface FacturaFormProps {
  onSubmit: (formData: FormData) => void;
  isSubmitting: boolean;
  docentes: { value: string; label: string }[];
}

export function FacturaForm({ onSubmit, isSubmitting, docentes }: FacturaFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<FacturaFormData>({
    resolver: zodResolver(facturaSchema),
  });

  const selectedFile = watch('archivo');

  const handleFormSubmit = (data: FacturaFormData) => {
    const formData = new FormData();
    formData.append('docente_id', data.docente_id);
    formData.append('periodo', data.periodo);
    formData.append('detalle', data.detalle);
    formData.append('archivo', data.archivo);
    onSubmit(formData);
    reset();
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div className="w-full">
        <label className="mb-1 block text-sm font-medium text-secondary-700">Docente</label>
        <select
          {...register('docente_id')}
          className="block w-full rounded-lg border border-secondary-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1"
        >
          <option value="">Seleccionar docente</option>
          {docentes.map((d) => (
            <option key={d.value} value={d.value}>{d.label}</option>
          ))}
        </select>
        {errors.docente_id && (
          <p className="mt-1 text-sm text-danger-600" role="alert">{errors.docente_id.message}</p>
        )}
      </div>

      <Input label="Período (AAAA-MM)" placeholder="2026-06" error={errors.periodo?.message} {...register('periodo')} />
      <Input label="Detalle" error={errors.detalle?.message} {...register('detalle')} />

      <FacturaFileInput
        error={errors.archivo?.message}
        selectedFile={selectedFile}
        onFileSelect={(file) => setValue('archivo', file, { shouldValidate: true })}
      />

      <Button type="submit" isLoading={isSubmitting}>
        Cargar Factura
      </Button>
    </form>
  );
}
