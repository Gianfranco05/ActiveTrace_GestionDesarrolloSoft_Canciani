import { clsx } from 'clsx';
import { type TextareaHTMLAttributes, forwardRef } from 'react';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const textareaId = id ?? `textarea-${label.toLowerCase().replace(/\s+/g, '-')}`;

    return (
      <div className="w-full">
        <label
          htmlFor={textareaId}
          className="mb-1 block text-sm font-medium text-secondary-700"
        >
          {label}
        </label>
        <textarea
          ref={ref}
          id={textareaId}
          className={clsx(
            'block w-full rounded-lg border px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-secondary-400 focus:outline-none focus:ring-2 focus:ring-offset-1',
            error
              ? 'border-danger-300 focus:border-danger-500 focus:ring-danger-500'
              : 'border-secondary-300 focus:border-primary-500 focus:ring-primary-500',
            props.disabled && 'cursor-not-allowed bg-secondary-50 text-secondary-500',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${textareaId}-error` : undefined}
          {...props}
        />
        {error && (
          <p id={`${textareaId}-error`} className="mt-1 text-sm text-danger-600" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
