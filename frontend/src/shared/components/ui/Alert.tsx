import { clsx } from 'clsx';
import { type ReactNode } from 'react';

type AlertVariant = 'success' | 'error' | 'warning' | 'info';

interface AlertProps {
  variant?: AlertVariant;
  children: ReactNode;
  className?: string;
}

const variantStyles: Record<AlertVariant, string> = {
  success: 'bg-success-50 text-success-800 border-success-200',
  error: 'bg-danger-50 text-danger-800 border-danger-200',
  warning: 'bg-amber-50 text-amber-800 border-amber-200',
  info: 'bg-primary-50 text-primary-800 border-primary-200',
};

export function Alert({ variant = 'info', children, className }: AlertProps) {
  return (
    <div
      className={clsx(
        'rounded-lg border px-4 py-3 text-sm',
        variantStyles[variant],
        className
      )}
      role="alert"
    >
      {children}
    </div>
  );
}
