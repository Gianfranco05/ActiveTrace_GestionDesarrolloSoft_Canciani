import { useState } from 'react';

import { MateriaSelector } from '@/features/academico/components/MateriaSelector';
import { useUploadReporteFinalizacion, useExportEntregasSinCorregir } from '@/features/academico/hooks/useEntregasSinCorregir';
import { useMateriaSeleccionada } from '@/features/academico/hooks/useMateriaSeleccionada';
import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { FileUpload } from '@/shared/components/ui/FileUpload';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';

import type { EntradaMonitor } from '@/features/academico/types/analisis.types';

type PageState = 'idle' | 'uploading' | 'success' | 'error';

export function DeteccionEntregasPage() {
  const [materiaId, setMateriaId] = useMateriaSeleccionada();
  const [pageState, setPageState] = useState<PageState>('idle');
  const [progress, setProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState('');
  const [entregas, setEntregas] = useState<EntradaMonitor[]>([]);

  const uploadMutation = useUploadReporteFinalizacion();
  const exportMutation = useExportEntregasSinCorregir();

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
          setPageState('success');
          setEntregas((data as any)?.items ?? []);
        },
        onError: (err) => {
          setErrorMsg(err instanceof Error ? err.message : 'Error al procesar el reporte');
          setPageState('error');
        },
      }
    );
  };

  const handleExport = () => {
    if (materiaId) {
      exportMutation.mutate(materiaId);
    }
  };

  const columns: Column[] = [
    { key: 'alumno_nombre', header: 'Alumno', sortable: true },
    { key: 'actividad', header: 'Actividad', sortable: true },
    {
      key: 'estado',
      header: 'Estado',
      sortable: true,
      render: (item) => <StatusBadge status={item.estado ?? ''} />,
    },
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Detección de Entregas sin Corregir</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Subí el reporte de finalización del LMS para detectar entregas sin corregir
        </p>
      </div>

      <Card>
        <div className="space-y-4">
          <MateriaSelector
            value={materiaId}
            onChange={(id) => {
              setMateriaId(id);
              setPageState('idle');
            }}
          />

          {materiaId && pageState !== 'success' && (
            <FileUpload
              accept=".csv,.xlsx"
              maxSizeMB={20}
              onUpload={handleUpload}
              uploading={pageState === 'uploading'}
              progress={progress}
            />
          )}

          {pageState === 'uploading' && (
            <div className="flex flex-col items-center gap-2 py-4">
              <Spinner size="md" />
              <p className="text-sm text-secondary-600">Procesando reporte...</p>
              <div className="h-2 w-full max-w-xs overflow-hidden rounded-full bg-secondary-200">
                <div
                  className="h-full rounded-full bg-primary-600 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-xs text-secondary-500">{progress}%</span>
            </div>
          )}

          {pageState === 'success' && (
            <Alert variant="success">
              Reporte procesado correctamente. Las entregas sin corregir se actualizaron.
            </Alert>
          )}

          {errorMsg && (
            <Alert variant="error">
              <p>{errorMsg}</p>
              <Button variant="secondary" size="sm" onClick={() => setPageState('idle')} className="mt-2">
                Volver a intentar
              </Button>
            </Alert>
          )}

          {pageState === 'uploading' && (
            <div className="flex items-center justify-center py-8">
              <Spinner size="lg" />
            </div>
          )}

          {pageState === 'error' && (
            <Alert variant="error">
              {errorMsg || 'Error al cargar las entregas sin corregir'}
            </Alert>
          )}

          {pageState === 'success' && entregas.length > 0 && (
            <>
              <DataTable
                columns={columns}
                data={entregas}
                keyExtractor={(e, i) => `${e.alumno_nombre ?? 'alumno'}-${e.actividad ?? ''}-${i}`}
                pageSize={15}
                emptyMessage="No se detectaron entregas sin corregir"
              />
              <Button
                variant="secondary"
                onClick={handleExport}
                disabled={entregas.length === 0 || exportMutation.isPending}
                isLoading={exportMutation.isPending}
              >
                Exportar (.xlsx)
              </Button>
            </>
          )}

          {!materiaId && (
            <p className="py-4 text-center text-sm text-secondary-400">
              Seleccioná una materia para empezar
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
