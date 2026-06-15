import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';

const twoFactorSchema = z.object({
  code: z
    .string()
    .length(6, 'El código debe tener 6 dígitos')
    .regex(/^\d{6}$/, 'El código debe tener 6 dígitos'),
});

type TwoFactorFormValues = z.infer<typeof twoFactorSchema>;

interface TwoFactorFormProps {
  onSubmit: (data: TwoFactorFormValues) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export function TwoFactorForm({ onSubmit, isLoading, error }: TwoFactorFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TwoFactorFormValues>({
    resolver: zodResolver(twoFactorSchema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {error && (
        <Alert variant="error">{error}</Alert>
      )}

      <p className="text-sm text-secondary-600">
        Ingresá el código de verificación de tu aplicación de autenticación
      </p>

      <Input
        label="Código de verificación"
        placeholder="000000"
        maxLength={6}
        inputMode="numeric"
        autoComplete="one-time-code"
        error={errors.code?.message}
        {...register('code')}
      />

      <Button type="submit" isLoading={isLoading} className="w-full" size="lg">
        {isLoading ? 'Verificando...' : 'Verificar'}
      </Button>
    </form>
  );
}
