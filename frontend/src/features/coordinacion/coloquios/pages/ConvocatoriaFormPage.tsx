import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

import { useCrearConvocatoria } from '@/features/coordinacion/coloquios/hooks/useColoquios';
import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Select } from '@/shared/components/ui/Select';
import api from '@/shared/services/api';

interface CupoPorDiaForm {
  fecha: string;
  cupo: number;
}

const TIPO_OPTIONS = [
  { value: 'Parcial', label: 'Parcial' },
  { value: 'TP', label: 'TP' },
  { value: 'Coloquio', label: 'Coloquio' },
  { value: 'Recuperatorio', label: 'Recuperatorio' },
];

export function ConvocatoriaFormPage() {
  const navigate = useNavigate();
  const [materiaId, setMateriaId] = useState('');
  const [cohorteId, setCohorteId] = useState('');
  const [tipo, setTipo] = useState<'Parcial' | 'TP' | 'Coloquio' | 'Recuperatorio'>('Coloquio');
  const [instancia, setInstancia] = useState('');
  const [cuposPorDia, setCuposPorDia] = useState<CupoPorDiaForm[]>([{ fecha: '', cupo: 10 }]);
  const [error, setError] = useState<string | null>(null);
  const { mutateAsync, isPending } = useCrearConvocatoria();

  const { data: materias = [] } = useQuery<{ id: string; nombre: string; codigo: string }[]>({
    queryKey: ['materias-coloquio'],
    queryFn: async () => {
      const { data } = await api.get<{ items: { id: string; nombre: string; codigo: string }[] }>('/v1/estructura/materias');
      return data.items ?? [];
    },
  });

  const { data: cohortes = [] } = useQuery<{ id: string; nombre: string }[]>({
    queryKey: ['cohortes-coloquio'],
    queryFn: async () => {
      const { data } = await api.get<{ items: { id: string; nombre: string }[] }>('/v1/estructura/cohortes');
      return data.items ?? [];
    },
  });

  const addDia = () => {
    setCuposPorDia((prev) => [...prev, { fecha: '', cupo: 10 }]);
  };

  const removeDia = (idx: number) => {
    setCuposPorDia((prev) => prev.filter((_, i) => i !== idx));
  };

  const updateDia = (idx: number, field: keyof CupoPorDiaForm, value: string | number) => {
    setCuposPorDia((prev) => prev.map((d, i) => (i === idx ? { ...d, [field]: value } : d)));
  };

  const handleSubmit = async () => {
    setError(null);

    if (!materiaId || !cohorteId || !instancia.trim()) {
      setError('Todos los campos son obligatorios');
      return;
    }

    if (cuposPorDia.some((d) => d.cupo <= 0 || !d.fecha)) {
      setError('Cada día debe tener una fecha y un cupo mayor a 0');
      return;
    }

    try {
      await mutateAsync({
        materia_id: materiaId,
        cohorte_id: cohorteId,
        tipo,
        instancia: instancia.trim(),
        cupos_por_dia: cuposPorDia.map((d) => ({
          fecha: d.fecha,
          cupo: d.cupo,
        })),
      });
      navigate('/coordinacion/coloquios');
    } catch {
      setError('Error al crear la convocatoria');
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-secondary-900">Nueva Convocatoria</h1>

      {error && <Alert variant="error">{error}</Alert>}

      <Card>
        <div className="space-y-4">
          <Select
            label="Materia"
            placeholder="Seleccioná una materia"
            options={materias.map((m) => ({ value: m.id, label: `${m.codigo} — ${m.nombre}` }))}
            value={materiaId}
            onChange={(e) => setMateriaId(e.target.value)}
          />

          <Select
            label="Cohorte"
            placeholder="Seleccioná una cohorte"
            options={cohortes.map((c) => ({ value: c.id, label: c.nombre }))}
            value={cohorteId}
            onChange={(e) => setCohorteId(e.target.value)}
          />

          <Select
            label="Tipo"
            options={TIPO_OPTIONS}
            value={tipo}
            onChange={(e) => setTipo(e.target.value as typeof tipo)}
          />

          <Input
            label="Instancia"
            value={instancia}
            onChange={(e) => setInstancia(e.target.value)}
            placeholder="Ej: Coloquio Final — Diciembre 2026"
          />

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-secondary-700">Días y Cupos</h3>
              <Button type="button" variant="secondary" size="sm" onClick={addDia}>Agregar Día</Button>
            </div>

            {cuposPorDia.map((dia, idx) => (
              <div key={idx} className="grid grid-cols-3 gap-2 items-end rounded-lg bg-secondary-50 p-3">
                <Input label="Fecha" type="date" value={dia.fecha} onChange={(e) => updateDia(idx, 'fecha', e.target.value)} />
                <Input label="Cupo" type="number" min={1} value={dia.cupo} onChange={(e) => updateDia(idx, 'cupo', Number(e.target.value))} />
                <div className="pb-1">
                  <Button type="button" variant="danger" size="sm" onClick={() => removeDia(idx)} disabled={cuposPorDia.length === 1}>
                    X
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="secondary" type="button" onClick={() => navigate('/coordinacion/coloquios')}>Cancelar</Button>
            <Button onClick={handleSubmit} isLoading={isPending}>Crear Convocatoria</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
