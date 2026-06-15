import { clsx } from 'clsx';
import { type ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  header?: ReactNode;
  footer?: ReactNode;
  padding?: boolean;
}

export function Card({ children, className, header, footer, padding = true }: CardProps) {
  return (
    <div className={clsx('overflow-hidden rounded-xl bg-white shadow-md', className)}>
      {header && (
        <div className="border-b border-secondary-200 px-6 py-4">{header}</div>
      )}
      <div className={clsx(padding && 'px-6 py-4')}>{children}</div>
      {footer && (
        <div className="border-t border-secondary-200 px-6 py-4">{footer}</div>
      )}
    </div>
  );
}
