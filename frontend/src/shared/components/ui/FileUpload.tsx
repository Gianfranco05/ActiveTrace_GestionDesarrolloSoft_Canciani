import { clsx } from 'clsx';
import { type ReactNode, useRef, useState } from 'react';

import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Spinner } from '@/shared/components/ui/Spinner';

interface FileUploadProps {
  accept?: string;
  maxSizeMB?: number;
  onFileSelect?: (file: File) => void;
  onUpload?: (file: File) => void;
  uploading?: boolean;
  progress?: number;
  isLoading?: boolean;
  label?: string;
  error?: string;
  disabled?: boolean;
  children?: ReactNode;
}

export function FileUpload({
  accept,
  maxSizeMB = 20,
  onFileSelect,
  onUpload,
  uploading = false,
  progress = 0,
  isLoading = false,
  label = 'Seleccionar archivo',
  error: externalError,
  disabled = false,
  children,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [internalError, setInternalError] = useState<string | null>(null);

  const error = externalError ?? internalError;
  const hasAdvanced = !!onUpload;

  const validateFile = (file: File): string | null => {
    if (maxSizeMB > 0 && file.size > maxSizeMB * 1024 * 1024) {
      return `El archivo supera el tamaño máximo de ${maxSizeMB}MB`;
    }
    if (accept) {
      const ext = file.name.split('.').pop()?.toLowerCase();
      const allowedExts = accept.split(',').map((e) => e.trim().replace('.', '').toLowerCase());
      if (!ext || !allowedExts.includes(ext)) {
        return `Tipo de archivo no soportado. Usá: ${accept}`;
      }
    }
    return null;
  };

  const handleFile = (file: File) => {
    setInternalError(null);
    setFileName(file.name);
    const validationError = validateFile(file);
    if (validationError) {
      setInternalError(validationError);
      return;
    }
    if (onUpload) {
      onUpload(file);
    } else {
      onFileSelect?.(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleClick = () => inputRef.current?.click();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = '';
  };

  if (hasAdvanced) {
    return (
      <div>
        <div
          className={clsx(
            'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors',
            dragOver
              ? 'border-primary-500 bg-primary-50'
              : 'border-secondary-300 hover:border-secondary-400',
            disabled && 'cursor-not-allowed opacity-50'
          )}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={disabled ? undefined : handleClick}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleClick(); }}
        >
          <input
            ref={inputRef}
            type="file"
            accept={accept}
            onChange={handleChange}
            className="hidden"
            disabled={disabled}
          />
          {uploading ? (
            <div className="flex flex-col items-center gap-3">
              <Spinner size="md" />
              <span className="text-sm text-secondary-600">Subiendo archivo...</span>
              <div className="h-2 w-64 overflow-hidden rounded-full bg-secondary-200">
                <div
                  className="h-full rounded-full bg-primary-600 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-xs text-secondary-500">{progress}%</span>
            </div>
          ) : (
            <>
              <svg className="mb-2 h-10 w-10 text-secondary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-sm text-secondary-600">
                Arrastrá el archivo acá o <span className="font-medium text-primary-600">seleccionalo</span>
              </p>
              <p className="mt-1 text-xs text-secondary-400">{accept ?? '.csv,.xlsx'} — máximo {maxSizeMB}MB</p>
            </>
          )}
        </div>
        {children}
        {error && (
          <Alert variant="error" className="mt-2">
            {error}
          </Alert>
        )}
      </div>
    );
  }

  return (
    <div className="w-full">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        className="hidden"
      />
      <Button
        type="button"
        variant="secondary"
        onClick={handleClick}
        isLoading={isLoading}
      >
        {label}
      </Button>
      {fileName && (
        <p className="mt-1 text-sm text-secondary-500">{fileName}</p>
      )}
      {error && (
        <p className="mt-1 text-sm text-danger-600" role="alert">{error}</p>
      )}
      {children && <div className="mt-2">{children}</div>}
    </div>
  );
}
