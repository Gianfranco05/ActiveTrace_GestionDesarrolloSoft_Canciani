import { useNavigate, useSearchParams } from 'react-router-dom';

import { LoginForm } from '@/features/auth/components/LoginForm';
import { Card } from '@/shared/components/ui/Card';
import { useAuth } from '@/shared/hooks/useAuth';
import { TEMP_TOKEN_KEY, TEMP_TOKEN_PENDING } from '@/shared/utils/auth-constants';

export function LoginPage() {
  const { login, isLoading, error } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const handleSubmit = async (data: { email: string; password: string }) => {
    try {
      const result = await login(data.email, data.password);
      if (result.requires_2fa) {
        sessionStorage.setItem(TEMP_TOKEN_KEY, TEMP_TOKEN_PENDING);
        navigate('/auth/2fa', { replace: true });
      } else {
        const returnUrl = searchParams.get('returnUrl') ?? '/dashboard';
        navigate(returnUrl, { replace: true });
      }
    } catch {
      // Error is handled by AuthContext
    }
  };

  return (
    <Card className="w-full max-w-md">
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-secondary-900">activia trace</h1>
        <p className="mt-1 text-sm text-secondary-500">Iniciá sesión para continuar</p>
      </div>
      <LoginForm onSubmit={handleSubmit} isLoading={isLoading} error={error} />
    </Card>
  );
}
