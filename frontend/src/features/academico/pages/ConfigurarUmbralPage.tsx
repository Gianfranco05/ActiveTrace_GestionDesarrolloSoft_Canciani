import { useState, useEffect } from 'react';

import { MateriaSelector } from '@/features/academico/components/MateriaSelector';
import { useMateriaSeleccionada } from '@/features/academico/hooks/useMateriaSeleccionada';
import { useUmbral, useSetUmbral } from '@/features/academico/hooks/useUmbral';
import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Spinner } from '@/shared/components/ui/Spinner';

export function ConfigurarUmbralPage() {
  const [materiaId, setMateriaId] = useMateriaSeleccionada();
  const [porcentaje, setPorcentaje] = useState('60');
  const [successMsg, setSuccessMsg] = useState('');

  const { data: umbral, isLoading, error } = useUmbral(materiaId);
  const setUmbralMutation = useSetUmbral();

  useEffect(() => {
    if (umbral) {
      setPorcentaje(String(umbral.porcentaje));
    }
  }, [umbral]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMsg('');

    const val = parseInt(porcentaje, 10);
    if (isNaN(val) || val < 0 || val > 100) return;

    setUmbralMutation.mutate(
      { materiaId, porcentaje: val },
      {
        onSuccess: () => {
          setSuccessMsg('Umbral actualizado correctamente');
        },
      }
    );
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Configurar Umbral de Aprobación</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Definí el porcentaje mínimo de actividades aprobadas para considerar al alumno como regular
        </p>
      </div>

      <Card>
        <div className="space-y-4">
          <MateriaSelector
            value={materiaId}
            onChange={setMateriaId}
          />

          {isLoading && materiaId && (
            <div className="flex items-center gap-2 py-4">
              <Spinner size="sm" />
              <span className="text-sm text-secondary-500">Cargando configuración actual...</span>
            </div>
          )}

          {error && materiaId && (
            <Alert variant="error">Error al cargar la configuración actual</Alert>
          )}

          {umbral?.tieneCalificaciones && (
            <Alert variant="info">
              Esta materia ya tiene calificaciones importadas. Cambiar el umbral afectará los
              cálculos existentes.
            </Alert>
          )}

          {successMsg && (
            <Alert variant="success">{successMsg}</Alert>
          )}

          {setUmbralMutation.isError && (
            <Alert variant="error">
              {setUmbralMutation.error instanceof Error
                ? setUmbralMutation.error.message
                : 'Error al guardar el umbral'}
            </Alert>
          )}

          {materiaId && !isLoading && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Porcentaje mínimo de aprobación"
                type="number"
                min={0}
                max={100}
                value={porcentaje}
                onChange={(e) => setPorcentaje(e.target.value)}
                error={
                  (porcentaje && (isNaN(parseInt(porcentaje, 10)) || parseInt(porcentaje, 10) < 0 || parseInt(porcentaje, 10) > 100))
                    ? 'El valor debe estar entre 0 y 100'
                    : undefined
                }
              />
              <p className="text-xs text-secondary-400">
                Valor recomendado: 60%
              </p>
              <Button
                type="submit"
                isLoading={setUmbralMutation.isPending}
                disabled={!porcentaje || isNaN(parseInt(porcentaje, 10)) || parseInt(porcentaje, 10) < 0 || parseInt(porcentaje, 10) > 100}
              >
                Guardar umbral
              </Button>
            </form>
          )}

          {!materiaId && (
            <p className="py-4 text-center text-sm text-secondary-400">
              Seleccioná una materia para configurar su umbral
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
