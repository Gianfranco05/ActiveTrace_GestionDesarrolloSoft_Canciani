import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';

const forgotSchema = z.object({
  email: z.string().email('Email inválido'),
});

type ForgotFormValues = z.infer<typeof forgotSchema>;

interface ForgotPasswordFormProps {
  onSubmit: (data: ForgotFormValues) => Promise<void>;
  isLoading: boolean;
  isSuccess: boolean;
  error: string | null;
}

export function ForgotPasswordForm({
  onSubmit,
  isLoading,
  isSuccess,
  error,
}: ForgotPasswordFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotFormValues>({
    resolver: zodResolver(forgotSchema),
  });

  if (isSuccess) {
    return (
      <Alert variant="success">
        Si el email está registrado, recibirás un enlace para restablecer tu contraseña
      </Alert>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {error && (
        <Alert variant="error">{error}</Alert>
      )}

      <p className="text-sm text-secondary-600">
        Ingresá tu email y te enviaremos un enlace para restablecer tu contraseña
      </p>

      <Input
        label="Email"
        type="email"
        placeholder="tu@email.com"
        autoComplete="email"
        error={errors.email?.message}
        {...register('email')}
      />

      <Button type="submit" isLoading={isLoading} className="w-full" size="lg">
        {isLoading ? 'Enviando...' : 'Enviar enlace'}
      </Button>
    </form>
  );
}
