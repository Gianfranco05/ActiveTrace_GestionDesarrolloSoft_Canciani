import { useNavigate, Link } from 'react-router-dom';

import { TwoFactorForm } from '@/features/auth/components/TwoFactorForm';
import { Card } from '@/shared/components/ui/Card';
import { useAuth } from '@/shared/hooks/useAuth';

export function TwoFactorPage() {
  const { verify2FA, isLoading, error } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (data: { code: string }) => {
    try {
      await verify2FA(data.code);
      navigate('/dashboard', { replace: true });
    } catch {
      // Error is handled by AuthContext
    }
  };

  return (
    <Card className="w-full max-w-md">
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-secondary-900">Verificación en dos pasos</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Autenticación de dos factores
        </p>
      </div>
      <TwoFactorForm onSubmit={handleSubmit} isLoading={isLoading} error={error} />
      <div className="mt-4 text-center">
        <Link
          to="/auth/login"
          className="text-sm text-primary-600 hover:text-primary-500"
        >
          Volver al inicio de sesión
        </Link>
      </div>
    </Card>
  );
}
