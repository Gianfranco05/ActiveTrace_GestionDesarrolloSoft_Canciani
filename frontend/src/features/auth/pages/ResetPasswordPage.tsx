import { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';

import { ResetPasswordForm } from '@/features/auth/components/ResetPasswordForm';
import * as authService from '@/features/auth/services/auth.service';
import { Alert } from '@/shared/components/ui/Alert';
import { Card } from '@/shared/components/ui/Card';

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: { password: string }) => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      await authService.resetPassword(token, data.password);
      setIsSuccess(true);
    } catch {
      setError('Enlace inválido o expirado');
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <Card className="w-full max-w-md">
        <Alert variant="error">Enlace inválido o expirado</Alert>
        <div className="mt-4 text-center">
          <Link
            to="/auth/forgot"
            className="text-sm text-primary-600 hover:text-primary-500"
          >
            Solicitar un nuevo enlace
          </Link>
        </div>
      </Card>
    );
  }

  if (isSuccess) {
    return (
      <Card className="w-full max-w-md">
        <Alert variant="success">Contraseña restablecida exitosamente</Alert>
        <div className="mt-4 text-center">
          <Link
            to="/auth/login"
            className="text-sm font-medium text-primary-600 hover:text-primary-500"
          >
            Iniciar sesión
          </Link>
        </div>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-secondary-900">
          Restablecer contraseña
        </h1>
        <p className="mt-1 text-sm text-secondary-500">
          Ingresá tu nueva contraseña
        </p>
      </div>
      <ResetPasswordForm onSubmit={handleSubmit} isLoading={isLoading} error={error} />
    </Card>
  );
}
