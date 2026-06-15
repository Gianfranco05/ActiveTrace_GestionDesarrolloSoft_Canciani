import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AtrasadosTable } from '@/features/academico/components/AtrasadosTable';
import { MateriaSelector } from '@/features/academico/components/MateriaSelector';
import { useAtrasados } from '@/features/academico/hooks/useAtrasados';
import { useMateriaSeleccionada } from '@/features/academico/hooks/useMateriaSeleccionada';
import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Spinner } from '@/shared/components/ui/Spinner';

export function VistaAtrasadosPage() {
  const [materiaId, setMateriaId] = useMateriaSeleccionada();
  const navigate = useNavigate();
  const [seleccionados, setSeleccionados] = useState<string[]>([]);
  const [minFaltantes, setMinFaltantes] = useState('');
  const [maxPorcentaje, setMaxPorcentaje] = useState('');

  const filtros = {
    ...(minFaltantes ? { minFaltantes: parseInt(minFaltantes, 10) } : {}),
    ...(maxPorcentaje ? { maxPorcentaje: parseInt(maxPorcentaje, 10) } : {}),
  };

  const { data: atrasados, isLoading, error } = useAtrasados(materiaId, filtros);

  const handleToggle = (id: string) => {
    setSeleccionados((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const handleToggleAll = () => {
    if (!atrasados) return;
    setSeleccionados((prev) =>
      prev.length === atrasados.length ? [] : atrasados.map((a) => a.entrada_padron_id)
    );
  };

  const handleComunicar = () => {
    if (seleccionados.length === 0) return;
    navigate(`/academico/comunicaciones?alumnosIds=${seleccionados.join(',')}&materiaId=${materiaId}`);
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Alumnos Atrasados</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Visualizá los alumnos con actividades pendientes o por debajo del umbral
        </p>
      </div>

      <Card>
        <div className="space-y-4">
          <MateriaSelector
            value={materiaId}
            onChange={(id) => {
              setMateriaId(id);
              setSeleccionados([]);
            }}
          />

          {materiaId && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                label="Mín. actividades faltantes"
                type="number"
                min={0}
                placeholder="0"
                value={minFaltantes}
                onChange={(e) => setMinFaltantes(e.target.value)}
              />
              <Input
                label="Máx. % aprobación"
                type="number"
                min={0}
                max={100}
                placeholder="100"
                value={maxPorcentaje}
                onChange={(e) => setMaxPorcentaje(e.target.value)}
              />
            </div>
          )}

          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Spinner size="lg" />
            </div>
          )}

          {error && (
            <Alert variant="error" className="my-4">
              Error al cargar atrasados. Intentá de nuevo más tarde.
            </Alert>
          )}

          {atrasados && atrasados.length === 0 && !isLoading && (
            <Alert variant="info">
              {materiaId
                ? 'No hay alumnos atrasados en esta materia.'
                : 'Seleccioná una materia para ver los alumnos atrasados.'}
            </Alert>
          )}

          {atrasados && atrasados.length > 0 && (
            <>
              <AtrasadosTable
                atrasados={atrasados}
                seleccionados={seleccionados}
                onToggle={handleToggle}
                onToggleAll={handleToggleAll}
              />
              <div className="flex gap-3">
                <Button
                  onClick={handleComunicar}
                  disabled={seleccionados.length === 0}
                >
                  Comunicar ({seleccionados.length} seleccionados)
                </Button>
                {seleccionados.length > 0 && (
                  <Button
                    variant="ghost"
                    onClick={() => setSeleccionados([])}
                  >
                    Limpiar selección
                  </Button>
                )}
              </div>
            </>
          )}

          {!materiaId && (
            <p className="py-4 text-center text-sm text-secondary-400">
              Seleccioná una materia para ver los alumnos atrasados
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
