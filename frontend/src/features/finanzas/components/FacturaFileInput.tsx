import { useRef } from 'react';

import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';

interface FacturaFileInputProps {
  error?: string;
  selectedFile?: File;
  onFileSelect: (file: File) => void;
}

export function FacturaFileInput({ error, selectedFile, onFileSelect }: FacturaFileInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFileSelect(file);
  };

  return (
    <div className="w-full">
      <label className="mb-1 block text-sm font-medium text-secondary-700">
        Archivo PDF
      </label>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        onChange={handleChange}
        className="hidden"
      />
      <div className="flex items-center gap-3">
        <Button type="button" variant="secondary" size="sm" onClick={() => inputRef.current?.click()}>
          Seleccionar archivo
        </Button>
        {selectedFile && (
          <span className="text-sm text-secondary-600">
            {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
          </span>
        )}
      </div>
      {error && (
        <Alert variant="error" className="mt-2">{error}</Alert>
      )}
    </div>
  );
}
