import { clsx } from 'clsx';
import { type InputHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const inputId = id ?? `input-${label.toLowerCase().replace(/\s+/g, '-')}`;

    return (
      <div className="w-full">
        <label
          htmlFor={inputId}
          className="mb-1 block text-sm font-medium text-secondary-700"
        >
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            'block w-full rounded-lg border px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-secondary-400 focus:outline-none focus:ring-2 focus:ring-offset-1',
            error
              ? 'border-danger-300 focus:border-danger-500 focus:ring-danger-500'
              : 'border-secondary-300 focus:border-primary-500 focus:ring-primary-500',
            props.disabled && 'cursor-not-allowed bg-secondary-50 text-secondary-500',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${inputId}-error` : undefined}
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="mt-1 text-sm text-danger-600" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
