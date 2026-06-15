import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';

import { Card } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useAuth } from '@/shared/hooks/useAuth';
import api from '@/shared/services/api';

interface DashboardStats {
  usuarios: string;
  auditoria: string;
  permisos: string;
  roles: string;
}

const PLACEHOLDER = '—';

export function DashboardPage() {
  const { user, isLoading, roles, permissions } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    usuarios: PLACEHOLDER,
    auditoria: PLACEHOLDER,
    permisos: PLACEHOLDER,
    roles: PLACEHOLDER,
  });

  const isAdmin = roles.includes('ADMIN');

  useEffect(() => {
    if (isLoading) return;

    setStats((prev) => ({
      ...prev,
      permisos: String(permissions.length),
      roles: String(roles.length),
    }));

    if (isAdmin) {
      const fetchAdminStats = async () => {
        try {
          const [usuariosRes, auditRes] = await Promise.allSettled([
            api.get('/v1/admin/usuarios?limit=1'),
            api.get('/auditoria/log?limit=1'),
          ]);

          setStats((prev) => ({
            ...prev,
            usuarios:
              usuariosRes.status === 'fulfilled'
                ? String(usuariosRes.value.data.total ?? PLACEHOLDER)
                : PLACEHOLDER,
            auditoria:
              auditRes.status === 'fulfilled'
                ? String(auditRes.value.data.total ?? PLACEHOLDER)
                : PLACEHOLDER,
          }));
        } catch {
          // Silently handle — data stays as placeholder
        }
      };

      fetchAdminStats();
    }
  }, [isLoading, isAdmin, permissions.length, roles.length]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  if (roles.includes('ALUMNO') && !roles.includes('ADMIN') && !roles.includes('COORDINADOR')) {
    return <Navigate to="/alumno" replace />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">
          Bienvenido, {user?.name ?? 'Usuario'}
        </h1>
        <p className="mt-1 text-sm text-secondary-500">
          Panel principal de activia trace
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {isAdmin ? (
          <>
            <Card>
              <div className="text-center">
                <p className="text-3xl font-bold text-primary-600">{stats.usuarios}</p>
                <p className="mt-1 text-sm text-secondary-500">Usuarios totales</p>
              </div>
            </Card>
            <Card>
              <div className="text-center">
                <p className="text-3xl font-bold text-primary-600">{stats.auditoria}</p>
                <p className="mt-1 text-sm text-secondary-500">Registros de auditoría</p>
              </div>
            </Card>
            <Card>
              <div className="text-center">
                <p className="text-3xl font-bold text-primary-600">{stats.permisos}</p>
                <p className="mt-1 text-sm text-secondary-500">Permisos del sistema</p>
              </div>
            </Card>
            <Card>
              <div className="text-center">
                <p className="text-3xl font-bold text-primary-600">{stats.roles}</p>
                <p className="mt-1 text-sm text-secondary-500">Roles del sistema</p>
              </div>
            </Card>
          </>
        ) : (
          <>
            <Card>
              <div className="text-center">
                <p className="text-3xl font-bold text-primary-600">{stats.roles}</p>
                <p className="mt-1 text-sm text-secondary-500">Roles asignados</p>
              </div>
            </Card>
            <Card>
              <div className="text-center">
                <p className="text-3xl font-bold text-primary-600">{stats.permisos}</p>
                <p className="mt-1 text-sm text-secondary-500">Permisos</p>
              </div>
            </Card>
            <Card>
              <div className="text-center">
                <p className="text-3xl font-bold text-primary-600">{PLACEHOLDER}</p>
                <p className="mt-1 text-sm text-secondary-500">Encuentros</p>
              </div>
            </Card>
            <Card>
              <div className="text-center">
                <p className="text-3xl font-bold text-primary-600">{PLACEHOLDER}</p>
                <p className="mt-1 text-sm text-secondary-500">Equipos</p>
              </div>
            </Card>
          </>
        )}
      </div>

      {roles.length > 0 && (
        <Card>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-secondary-700">Tus roles:</span>
            <div className="flex gap-1">
              {roles.map((role) => (
                <span
                  key={role}
                  className="inline-flex items-center rounded-full bg-primary-100 px-2.5 py-0.5 text-xs font-medium text-primary-800"
                >
                  {role}
                </span>
              ))}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
