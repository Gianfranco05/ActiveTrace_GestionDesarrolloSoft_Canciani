import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { clsx } from 'clsx';
import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { z } from 'zod/v4';

import { useClonarEquipo, useMisMaterias } from '@/features/coordinacion/equipos/hooks/useEquipos';
import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Select } from '@/shared/components/ui/Select';
import api from '@/shared/services/api';

interface Option {
  value: string;
  label: string;
}

interface CarreraItem {
  id: string;
  codigo: string;
  nombre: string;
}

interface CohorteItem {
  id: string;
  nombre: string;
}

const schema = z.object({
  origen_materia_id: z.string().min(1, 'Seleccioná la materia origen'),
  origen_carrera_id: z.string().min(1, 'Seleccioná la carrera origen'),
  origen_cohorte_id: z.string().min(1, 'Seleccioná el cohorte origen'),
  destino_materia_id: z.string().min(1, 'Seleccioná la materia destino'),
  destino_carrera_id: z.string().min(1, 'Seleccioná la carrera destino'),
  destino_cohorte_id: z.string().min(1, 'Seleccioná el cohorte destino'),
  nueva_vig_desde: z.string().min(1, 'Ingresá la fecha de inicio'),
  nueva_vig_hasta: z.string().nullable(),
});

type FormValues = z.infer<typeof schema>;

const TOTAL_STEPS = 2;

export function ClonarEquipoPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const { mutateAsync, isPending, isSuccess, data } = useClonarEquipo();

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      origen_materia_id: '',
      origen_carrera_id: '',
      origen_cohorte_id: '',
      destino_materia_id: '',
      destino_carrera_id: '',
      destino_cohorte_id: '',
      nueva_vig_desde: '',
      nueva_vig_hasta: null,
    },
  });

  const {
    register,
    handleSubmit,
    watch,
    trigger,
    formState: { errors },
  } = form;

  const origenCarreraId = watch('origen_carrera_id');
  const destinoCarreraId = watch('destino_carrera_id');

  const { data: materias = [] } = useMisMaterias();

  const { data: carreras = [] } = useQuery<CarreraItem[]>({
    queryKey: ['carreras-clonar'],
    queryFn: async () => {
      const { data } = await api.get<{ items: CarreraItem[] }>('/v1/estructura/carreras');
      return data.items ?? [];
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data: cohortesOrigen = [] } = useQuery<CohorteItem[]>({
    queryKey: ['cohortes-clonar-origen', origenCarreraId],
    queryFn: async () => {
      const { data } = await api.get<{ items: CohorteItem[] }>('/v1/estructura/cohortes', {
        params: { carrera_id: origenCarreraId },
      });
      return data.items ?? [];
    },
    enabled: !!origenCarreraId,
  });

  const { data: cohortesDestino = [] } = useQuery<CohorteItem[]>({
    queryKey: ['cohortes-clonar-destino', destinoCarreraId],
    queryFn: async () => {
      const { data } = await api.get<{ items: CohorteItem[] }>('/v1/estructura/cohortes', {
        params: { carrera_id: destinoCarreraId },
      });
      return data.items ?? [];
    },
    enabled: !!destinoCarreraId,
  });

  const materiaOptions: Option[] = useMemo(
    () => materias.map((m) => ({ value: m.id, label: m.nombre })),
    [materias]
  );

  const carreraOptions: Option[] = useMemo(
    () => carreras.map((c) => ({ value: c.id, label: `${c.codigo} — ${c.nombre}` })),
    [carreras]
  );

  const cohorteOrigenOptions: Option[] = useMemo(
    () => cohortesOrigen.map((c) => ({ value: c.id, label: c.nombre })),
    [cohortesOrigen]
  );

  const cohorteDestinoOptions: Option[] = useMemo(
    () => cohortesDestino.map((c) => ({ value: c.id, label: c.nombre })),
    [cohortesDestino]
  );

  const stepFields: Record<number, (keyof FormValues)[]> = {
    1: ['origen_materia_id', 'origen_carrera_id', 'origen_cohorte_id'],
    2: ['destino_materia_id', 'destino_carrera_id', 'destino_cohorte_id', 'nueva_vig_desde'],
  };

  const handleNext = async () => {
    const fields = stepFields[step] ?? [];
    const valid = await trigger(fields);
    if (!valid) return;
    setStep((s) => Math.min(s + 1, TOTAL_STEPS));
  };

  const handlePrev = () => setStep((s) => Math.max(s - 1, 1));

  const onSubmit = async (values: FormValues) => {
    await mutateAsync({
      origen_materia_id: values.origen_materia_id,
      origen_carrera_id: values.origen_carrera_id,
      origen_cohorte_id: values.origen_cohorte_id,
      destino_materia_id: values.destino_materia_id,
      destino_carrera_id: values.destino_carrera_id,
      destino_cohorte_id: values.destino_cohorte_id,
      nueva_vig_desde: values.nueva_vig_desde,
      nueva_vig_hasta: values.nueva_vig_hasta || null,
    });
  };

  const asignacionesCreadas = data?.asignaciones.length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/coordinacion/equipos">
          <Button variant="secondary" size="sm">← Volver</Button>
        </Link>
        <h1 className="text-2xl font-bold text-secondary-900">Clonar Equipo Docente</h1>
      </div>

      <div className="flex items-center gap-2">
        {[1, 2].map((i) => (
          <div key={i} className="flex items-center">
            <div
              className={clsx(
                'flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium',
                step > i
                  ? 'bg-success-500 text-white'
                  : step === i
                    ? 'bg-primary-600 text-white'
                    : 'bg-secondary-200 text-secondary-600'
              )}
            >
              {step > i ? '✓' : i}
            </div>
            {i < 2 && (
              <div
                className={clsx(
                  'h-1 w-8',
                  step > i ? 'bg-success-500' : 'bg-secondary-200'
                )}
              />
            )}
          </div>
        ))}
      </div>
      <p className="text-sm text-secondary-500">
        Paso {step} de {TOTAL_STEPS}
      </p>

      {isSuccess ? (
        <Card>
          <Alert variant="success">
            Equipo clonado correctamente. {asignacionesCreadas} asignaciones creadas.
          </Alert>
          {asignacionesCreadas === 0 && (
            <p className="mt-2 text-sm text-amber-600">
              El equipo origen no tenía asignaciones vigentes para clonar
            </p>
          )}
          <div className="mt-4">
            <Button onClick={() => navigate('/coordinacion/equipos')}>Volver a Equipos</Button>
          </div>
        </Card>
      ) : (
        <Card>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {step === 1 && (
              <>
                <h2 className="text-lg font-semibold">Equipo Origen</h2>
                <Select
                  label="Materia origen"
                  placeholder="Seleccioná una materia"
                  options={materiaOptions}
                  error={errors.origen_materia_id?.message}
                  {...register('origen_materia_id')}
                />
                <Select
                  label="Carrera origen"
                  placeholder="Seleccioná una carrera"
                  options={carreraOptions}
                  error={errors.origen_carrera_id?.message}
                  {...register('origen_carrera_id')}
                />
                <Select
                  label="Cohorte origen"
                  placeholder={origenCarreraId ? 'Seleccioná un cohorte' : 'Primero seleccioná una carrera'}
                  options={cohorteOrigenOptions}
                  error={errors.origen_cohorte_id?.message}
                  disabled={!origenCarreraId}
                  {...register('origen_cohorte_id')}
                />
              </>
            )}

            {step === 2 && (
              <>
                <h2 className="text-lg font-semibold">Equipo Destino</h2>
                <Select
                  label="Materia destino"
                  placeholder="Seleccioná una materia"
                  options={materiaOptions}
                  error={errors.destino_materia_id?.message}
                  {...register('destino_materia_id')}
                />
                <Select
                  label="Carrera destino"
                  placeholder="Seleccioná una carrera"
                  options={carreraOptions}
                  error={errors.destino_carrera_id?.message}
                  {...register('destino_carrera_id')}
                />
                <Select
                  label="Cohorte destino"
                  placeholder={destinoCarreraId ? 'Seleccioná un cohorte' : 'Primero seleccioná una carrera'}
                  options={cohorteDestinoOptions}
                  error={errors.destino_cohorte_id?.message}
                  disabled={!destinoCarreraId}
                  {...register('destino_cohorte_id')}
                />
                <Input
                  label="Vigencia Desde"
                  type="date"
                  error={errors.nueva_vig_desde?.message}
                  {...register('nueva_vig_desde')}
                />
                <Input label="Vigencia Hasta" type="date" {...register('nueva_vig_hasta')} />
              </>
            )}

            <div className="flex justify-between">
              <Button variant="secondary" type="button" onClick={handlePrev} disabled={step === 1}>
                Anterior
              </Button>
              {step === 1 ? (
                <Button type="button" onClick={handleNext}>
                  Siguiente
                </Button>
              ) : (
                <Button type="submit" isLoading={isPending}>
                  Confirmar
                </Button>
              )}
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
