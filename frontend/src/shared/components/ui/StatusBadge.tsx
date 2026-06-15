import { clsx } from 'clsx';

type StatusVariant = 'active' | 'inactive' | 'pending' | 'progress' | 'resolved' | 'cancelled' | 'info' | 'warning' | 'error' | 'success';

interface StatusBadgeProps {
  status?: string;
  label?: string;
  variant?: StatusVariant;
  className?: string;
}

const statusColors: Record<string, string> = {
  Pendiente: 'bg-amber-100 text-amber-800',
  Enviando: 'bg-blue-100 text-blue-800',
  Enviado: 'bg-green-100 text-green-800',
  Error: 'bg-red-100 text-red-800',
  Cancelado: 'bg-gray-100 text-gray-600',
  Aprobado: 'bg-green-100 text-green-800',
  Desaprobado: 'bg-red-100 text-red-800',
  Activo: 'bg-green-100 text-green-800',
  Inactivo: 'bg-gray-100 text-gray-600',
};

const variantStyles: Record<StatusVariant, string> = {
  active: 'bg-success-100 text-success-700',
  inactive: 'bg-secondary-100 text-secondary-600',
  pending: 'bg-gray-100 text-gray-700',
  progress: 'bg-amber-100 text-amber-700',
  resolved: 'bg-success-100 text-success-700',
  cancelled: 'bg-danger-100 text-danger-700',
  info: 'bg-primary-100 text-primary-700',
  warning: 'bg-amber-100 text-amber-700',
  error: 'bg-danger-100 text-danger-700',
  success: 'bg-success-100 text-success-700',
};

export function StatusBadge({ status, label, variant, className }: StatusBadgeProps) {
  const displayText = label ?? status ?? '';
  const colorClass = variant
    ? variantStyles[variant]
    : status
      ? statusColors[status] ?? 'bg-gray-100 text-gray-700'
      : 'bg-gray-100 text-gray-700';

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        colorClass,
        className
      )}
    >
      {displayText}
    </span>
  );
}
