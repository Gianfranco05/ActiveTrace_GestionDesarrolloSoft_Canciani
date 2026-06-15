import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

import { ComunicacionPreview } from '@/features/academico/components/ComunicacionPreview';
import { ComunicacionTracker } from '@/features/academico/components/ComunicacionTracker';
import { useEnviarComunicacion, useEstadoComunicaciones, useCancelarComunicacion, usePreview } from '@/features/academico/hooks/useComunicaciones';
import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';

type PageView = 'preview' | 'tracking';

export function ComunicacionesPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [view, setView] = useState<PageView>('preview');
  const [loteId, setLoteId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  const alumnosIdsParam = searchParams.get('alumnosIds') ?? '';
  const materiaId = searchParams.get('materiaId') ?? '';
  const alumnosIds = alumnosIdsParam ? alumnosIdsParam.split(',') : [];

  const { data: previewData, isLoading: loadingPreview, error: previewError } = usePreview(alumnosIds);
  const enviarMutation = useEnviarComunicacion();
  const { data: trackingData, allInFinalState, isLoading: loadingTracking } = useEstadoComunicaciones(loteId);
  const cancelarMutation = useCancelarComunicacion();

  useEffect(() => {
    if (allInFinalState) {
      const timer = setTimeout(() => {}, 0);
      return () => clearTimeout(timer);
    }
  }, [allInFinalState]);

  const handleEnviar = () => {
    setErrorMsg('');
    enviarMutation.mutate(
      { alumnosIds, materiaId },
      {
        onSuccess: (data) => {
          setLoteId(data.loteId);
          setView('tracking');
        },
        onError: (err) => {
          setErrorMsg(err instanceof Error ? err.message : 'Error al enviar comunicaciones');
        },
      }
    );
  };

  const handleCancelar = () => {
    if (!loteId) return;
    cancelarMutation.mutate(loteId, {
      onSuccess: () => {
        navigate('/academico/atrasados' + (materiaId ? `?materiaId=${materiaId}` : ''));
      },
    });
  };

  const handleVolverAtrasados = () => {
    navigate('/academico/atrasados' + (materiaId ? `?materiaId=${materiaId}` : ''));
  };

  if (!alumnosIdsParam) {
    return (
      <div className="mx-auto max-w-4xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Comunicaciones</h1>
          <p className="mt-1 text-sm text-secondary-500">Envío de comunicaciones a alumnos atrasados</p>
        </div>
        <Card>
          <div className="py-8 text-center">
            <p className="text-secondary-500 mb-4">
              No hay alumnos seleccionados para comunicar.
            </p>
            <p className="text-sm text-secondary-400 mb-4">
              Seleccioná alumnos desde la vista de Atrasados y hace clic en "Comunicar".
            </p>
            <Button onClick={() => navigate('/academico/atrasados')}>
              Ir a Atrasados
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Comunicaciones</h1>
        <p className="mt-1 text-sm text-secondary-500">
          {view === 'preview' ? 'Previsualizá y confirmá el envío de comunicaciones' : 'Seguí el estado de las comunicaciones'}
        </p>
      </div>

      <Card>
        {view === 'preview' && (
          <div className="space-y-4">
            {loadingPreview && (
              <div className="flex items-center justify-center py-8">
                <Spinner size="lg" />
              </div>
            )}

            {previewError && (
              <Alert variant="error">
                Error al generar la previsualización de comunicaciones
              </Alert>
            )}

            {errorMsg && (
              <Alert variant="error">{errorMsg}</Alert>
            )}

            {previewData && (
              <>
                <ComunicacionPreview items={previewData} />
                <div className="flex gap-3">
                  <Button
                    onClick={handleEnviar}
                    isLoading={enviarMutation.isPending}
                    disabled={previewData.length === 0}
                  >
                    Confirmar y enviar
                  </Button>
                  <Button variant="secondary" onClick={handleVolverAtrasados}>
                    Cancelar
                  </Button>
                </div>
              </>
            )}
          </div>
        )}

        {view === 'tracking' && (
          <div className="space-y-4">
            {loadingTracking && (
              <div className="flex items-center justify-center py-8">
                <Spinner size="lg" />
              </div>
            )}

            {trackingData && (
              <>
                <ComunicacionTracker
                  estados={trackingData}
                  allInFinalState={allInFinalState}
                />
                <div className="flex gap-3">
                  {!allInFinalState && (
                    <Button variant="danger" onClick={handleCancelar} isLoading={cancelarMutation.isPending}>
                      Cancelar envío
                    </Button>
                  )}
                  {allInFinalState && (
                    <Button onClick={handleVolverAtrasados}>
                      Volver a Atrasados
                    </Button>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
