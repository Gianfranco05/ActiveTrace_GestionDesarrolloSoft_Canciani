import { type ReactNode } from 'react';

import { Card } from '@/shared/components/ui/Card';
import { useAuth } from '@/shared/hooks/useAuth';

interface RequirePermissionProps {
  requiredPermission: string | null;
  children: ReactNode;
  fallback?: ReactNode;
}

export function RequirePermission({
  requiredPermission,
  children,
  fallback,
}: RequirePermissionProps) {
  const { hasPermission } = useAuth();

  if (!requiredPermission) {
    return <>{children}</>;
  }

  if (!hasPermission(requiredPermission)) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <div className="flex items-center justify-center p-12">
        <Card className="max-w-md text-center">
          <div className="py-8">
            <h2 className="text-lg font-semibold text-secondary-900">
              Sin acceso
            </h2>
            <p className="mt-2 text-sm text-secondary-500">
              No tenés permisos para acceder a esta sección
            </p>
          </div>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
