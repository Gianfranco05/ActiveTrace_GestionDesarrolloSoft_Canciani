import { useState } from 'react';

import { ActividadesPreview } from '@/features/academico/components/ActividadesPreview';
import { MateriaSelector } from '@/features/academico/components/MateriaSelector';
import { useUploadCalificaciones, useConfirmarImportacion } from '@/features/academico/hooks/useCalificaciones';
import { useMateriaSeleccionada } from '@/features/academico/hooks/useMateriaSeleccionada';
import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { FileUpload } from '@/shared/components/ui/FileUpload';
import { Spinner } from '@/shared/components/ui/Spinner';

type PageState = 'idle' | 'uploading' | 'preview' | 'confirming' | 'success' | 'error';

export function ImportarCalificacionesPage() {
  const [materiaId, setMateriaId] = useMateriaSeleccionada();
  const [pageState, setPageState] = useState<PageState>('idle');
  const [progress, setProgress] = useState(0);
  const [uploadedData, setUploadedData] = useState<{ actividades: { id: string; nombre: string; fecha: string; alumnosCount: number; seleccionada: boolean }[] } | null>(null);
  const [seleccionadas, setSeleccionadas] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState('');

  const uploadMutation = useUploadCalificaciones();
  const confirmarMutation = useConfirmarImportacion();

  const handleUpload = (file: File) => {
    setErrorMsg('');
    setPageState('uploading');
    setProgress(0);

    const formData = new FormData();
    formData.append('archivo', file);
    if (materiaId) formData.append('materia_id', materiaId);

    uploadMutation.mutate(
      { formData, onProgress: setProgress },
      {
        onSuccess: (data) => {
          setUploadedData(data);
          setSeleccionadas(data.actividades.map((a) => a.id));
          setPageState('preview');
        },
        onError: (err) => {
          setErrorMsg(err instanceof Error ? err.message : 'Error al subir el archivo');
          setPageState('error');
        },
      }
    );
  };

  const handleToggleActividad = (id: string) => {
    setSeleccionadas((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const handleConfirmar = () => {
    if (!materiaId || seleccionadas.length === 0) return;
    setPageState('confirming');

    confirmarMutation.mutate(
      { materiaId, actividades: seleccionadas },
      {
        onSuccess: () => {
          setPageState('success');
        },
        onError: (err) => {
          setErrorMsg(err instanceof Error ? err.message : 'Error al confirmar la importación');
          setPageState('error');
        },
      }
    );
  };

  const handleReset = () => {
    setPageState('idle');
    setUploadedData(null);
    setSeleccionadas([]);
    setProgress(0);
    setErrorMsg('');
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Importar Calificaciones</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Subí el archivo de calificaciones del LMS para importar las actividades
        </p>
      </div>

      <Card>
        <div className="space-y-4">
          <MateriaSelector
            value={materiaId}
            onChange={(id) => {
              setMateriaId(id);
              if (pageState !== 'idle') handleReset();
            }}
            disabled={pageState === 'uploading' || pageState === 'confirming'}
          />

          {(pageState === 'idle' || pageState === 'error') && materiaId && (
            <FileUpload
              accept=".csv,.xlsx"
              maxSizeMB={20}
              onUpload={handleUpload}
              disabled={false}
            />
          )}

          {pageState === 'uploading' && (
            <div className="flex flex-col items-center gap-2 py-8">
              <Spinner size="lg" />
              <p className="text-sm text-secondary-600">Subiendo archivo...</p>
              <div className="h-2 w-full max-w-xs overflow-hidden rounded-full bg-secondary-200">
                <div
                  className="h-full rounded-full bg-primary-600 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-xs text-secondary-500">{progress}%</span>
            </div>
          )}

          {errorMsg && (
            <Alert variant="error">
              <p>{errorMsg}</p>
              <Button variant="secondary" size="sm" onClick={handleReset} className="mt-2">
                Volver a intentar
              </Button>
            </Alert>
          )}

          {pageState === 'preview' && uploadedData && (
            <>
              <ActividadesPreview
                actividades={uploadedData.actividades}
                seleccionadas={seleccionadas}
                onToggle={handleToggleActividad}
              />
              <div className="flex gap-3">
                <Button
                  onClick={handleConfirmar}
                  disabled={seleccionadas.length === 0 || confirmarMutation.isPending}
                  isLoading={confirmarMutation.isPending}
                >
                  Confirmar importación ({seleccionadas.length} actividades)
                </Button>
                <Button variant="secondary" onClick={handleReset}>
                  Cancelar
                </Button>
              </div>
            </>
          )}

          {pageState === 'confirming' && (
            <div className="flex flex-col items-center gap-2 py-8">
              <Spinner size="lg" />
              <p className="text-sm text-secondary-600">Guardando calificaciones...</p>
            </div>
          )}

          {pageState === 'success' && (
            <Alert variant="success">
              <p className="font-medium">¡Calificaciones importadas con éxito!</p>
              <p className="mt-1 text-sm">
                {seleccionadas.length} actividades fueron procesadas correctamente.
              </p>
              <Button onClick={handleReset} variant="secondary" size="sm" className="mt-3">
                Importar otro archivo
              </Button>
            </Alert>
          )}

          {pageState === 'idle' && !materiaId && (
            <p className="py-4 text-center text-sm text-secondary-400">
              Seleccioná una materia para empezar
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
