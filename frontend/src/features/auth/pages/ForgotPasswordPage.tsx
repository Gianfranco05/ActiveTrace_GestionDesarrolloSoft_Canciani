import { useState } from 'react';
import { Link } from 'react-router-dom';

import { ForgotPasswordForm } from '@/features/auth/components/ForgotPasswordForm';
import * as authService from '@/features/auth/services/auth.service';
import { Card } from '@/shared/components/ui/Card';

export function ForgotPasswordPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: { email: string }) => {
    setIsLoading(true);
    setError(null);
    try {
      await authService.forgotPassword(data.email);
      setIsSuccess(true);
    } catch {
      // Always show success message for security (don't reveal if email exists)
      setIsSuccess(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md">
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-secondary-900">Recuperar contraseña</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Te enviaremos un enlace para restablecer tu contraseña
        </p>
      </div>
      <ForgotPasswordForm
        onSubmit={handleSubmit}
        isLoading={isLoading}
        isSuccess={isSuccess}
        error={error}
      />
      {!isSuccess && (
        <div className="mt-4 text-center">
          <Link
            to="/auth/login"
            className="text-sm text-primary-600 hover:text-primary-500"
          >
            Volver al inicio de sesión
          </Link>
        </div>
      )}
      {isSuccess && (
        <div className="mt-4 text-center">
          <Link
            to="/auth/login"
            className="text-sm text-primary-600 hover:text-primary-500"
          >
            Volver al inicio de sesión
          </Link>
        </div>
      )}
    </Card>
  );
}
