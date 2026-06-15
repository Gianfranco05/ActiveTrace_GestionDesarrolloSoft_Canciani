import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { clsx } from 'clsx';
import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { z } from 'zod/v4';

import { useAsignacionMasiva, useMisMaterias } from '@/features/coordinacion/equipos/hooks/useEquipos';
import { Alert } from '@/shared/components/ui/Alert';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Select } from '@/shared/components/ui/Select';
import { Spinner } from '@/shared/components/ui/Spinner';
import api from '@/shared/services/api';

import type { UsuarioSearchResult } from '@/features/coordinacion/equipos/types/equipos.types';

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

interface RolItem {
  id: string;
  nombre: string;
}

const schema = z.object({
  materia_id: z.string().min(1, 'Seleccioná una materia'),
  carrera_id: z.string().min(1, 'Seleccioná una carrera'),
  cohorte_id: z.string().min(1, 'Seleccioná un cohorte'),
  rol_id: z.string().min(1, 'Seleccioná un rol'),
  usuario_ids: z.array(z.string()).min(1, 'Seleccioná al menos un docente'),
  vig_desde: z.string().min(1, 'Ingresá la fecha de inicio'),
  vig_hasta: z.string().nullable(),
  comisiones: z.string().nullable(),
});

type FormValues = z.infer<typeof schema>;

const TOTAL_STEPS = 4;

export function AsignacionMasivaPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const { mutateAsync, isPending, isSuccess } = useAsignacionMasiva();

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      materia_id: '',
      carrera_id: '',
      cohorte_id: '',
      rol_id: '',
      usuario_ids: [],
      vig_desde: '',
      vig_hasta: null,
      comisiones: null,
    },
  });

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    trigger,
    formState: { errors },
  } = form;

  const materiaId = watch('materia_id');
  const carreraId = watch('carrera_id');
  const cohorteId = watch('cohorte_id');
  const rolId = watch('rol_id');
  const usuarioIds = watch('usuario_ids');
  const vigDesde = watch('vig_desde');
  const vigHasta = watch('vig_hasta');

  const { data: materias = [] } = useMisMaterias();

  const { data: carreras = [] } = useQuery<CarreraItem[]>({
    queryKey: ['carreras-masiva'],
    queryFn: async () => {
      const { data } = await api.get<{ items: CarreraItem[] }>('/v1/estructura/carreras');
      return data.items ?? [];
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data: cohortes = [] } = useQuery<CohorteItem[]>({
    queryKey: ['cohortes-masiva', carreraId],
    queryFn: async () => {
      const { data } = await api.get<{ items: CohorteItem[] }>('/v1/estructura/cohortes', {
        params: { carrera_id: carreraId },
      });
      return data.items ?? [];
    },
    enabled: !!carreraId,
  });

  const { data: roles = [] } = useQuery<RolItem[]>({
    queryKey: ['roles-masiva'],
    queryFn: async () => {
      const { data } = await api.get<RolItem[]>('/v1/rbac/roles-names');
      return data;
    },
    staleTime: 5 * 60 * 1000,
  });

  const [userQuery, setUserQuery] = useState('');
  const [selectedUsers, setSelectedUsers] = useState<UsuarioSearchResult[]>([]);

  const { data: searchResults = [], isFetching: searching } = useQuery<UsuarioSearchResult[]>({
    queryKey: ['usuarios-search', userQuery],
    queryFn: async () => {
      const { data } = await api.get<{ items: UsuarioSearchResult[] }>('/equipos/usuarios/search', {
        params: { q: userQuery },
      });
      return data.items ?? [];
    },
    enabled: userQuery.length >= 2,
  });

  const materiaOptions: Option[] = useMemo(
    () => materias.map((m) => ({ value: m.id, label: m.nombre })),
    [materias]
  );

  const carreraOptions: Option[] = useMemo(
    () => carreras.map((c) => ({ value: c.id, label: `${c.codigo} — ${c.nombre}` })),
    [carreras]
  );

  const cohorteOptions: Option[] = useMemo(
    () => cohortes.map((c) => ({ value: c.id, label: c.nombre })),
    [cohortes]
  );

  const rolOptions: Option[] = useMemo(
    () => roles.map((r) => ({ value: r.id, label: r.nombre })),
    [roles]
  );

  const resolvedMateria = materias.find((m) => m.id === materiaId);
  const resolvedCarrera = carreras.find((c) => c.id === carreraId);
  const resolvedCohorte = cohortes.find((c) => c.id === cohorteId);
  const resolvedRol = roles.find((r) => r.id === rolId);

  const stepFields: Record<number, (keyof FormValues)[]> = {
    1: ['materia_id', 'carrera_id', 'cohorte_id'],
    2: ['rol_id', 'usuario_ids'],
    3: ['vig_desde'],
    4: [],
  };

  const handleNext = async () => {
    const fields = stepFields[step] ?? [];
    const valid = await trigger(fields);
    if (!valid) return;

    if (step === 2 && usuarioIds.length === 0) {
      return;
    }

    setStep((s) => Math.min(s + 1, TOTAL_STEPS));
  };

  const handlePrev = () => setStep((s) => Math.max(s - 1, 1));

  const toggleUser = (user: UsuarioSearchResult) => {
    setSelectedUsers((prev) => {
      const exists = prev.find((u) => u.id === user.id);
      if (exists) {
        return prev.filter((u) => u.id !== user.id);
      }
      return [...prev, user];
    });
    setValue(
      'usuario_ids',
      usuarioIds.includes(user.id)
        ? usuarioIds.filter((id) => id !== user.id)
        : [...usuarioIds, user.id],
      { shouldValidate: true }
    );
  };

  const onSubmit = async (values: FormValues) => {
    try {
      await mutateAsync({
        materia_id: values.materia_id,
        carrera_id: values.carrera_id,
        cohorte_id: values.cohorte_id,
        rol_id: values.rol_id,
        usuario_ids: values.usuario_ids,
        vig_desde: values.vig_desde,
        vig_hasta: values.vig_hasta || null,
        comisiones: values.comisiones || null,
      });
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 409) {
        setError('Ya existe una asignación para esta combinación de materia, carrera y cohorte');
      } else {
        setError('Error al realizar la asignación masiva');
      }
      return;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/coordinacion/equipos">
          <Button variant="secondary" size="sm">← Volver</Button>
        </Link>
        <h1 className="text-2xl font-bold text-secondary-900">Asignación Masiva</h1>
      </div>

      <div className="flex items-center gap-2">
        {Array.from({ length: TOTAL_STEPS }, (_, i) => (
          <div key={i} className="flex items-center">
            <div
              className={clsx(
                'flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium',
                step > i + 1
                  ? 'bg-success-500 text-white'
                  : step === i + 1
                    ? 'bg-primary-600 text-white'
                    : 'bg-secondary-200 text-secondary-600'
              )}
            >
              {step > i + 1 ? '✓' : i + 1}
            </div>
            {i < TOTAL_STEPS - 1 && (
              <div
                className={clsx(
                  'h-1 w-8',
                  step > i + 1 ? 'bg-success-500' : 'bg-secondary-200'
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
          <Alert variant="success">Asignación masiva creada correctamente</Alert>
          <div className="mt-4">
            <Button onClick={() => navigate('/coordinacion/equipos')}>Volver a Equipos</Button>
          </div>
        </Card>
      ) : (
        <Card>
          {error && <Alert variant="error" className="mb-4">{error}</Alert>}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {step === 1 && (
              <>
                <h2 className="text-lg font-semibold">Seleccionar Materia, Carrera y Cohorte</h2>
                <Select
                  label="Materia"
                  placeholder="Seleccioná una materia"
                  options={materiaOptions}
                  error={errors.materia_id?.message}
                  {...register('materia_id')}
                />
                <Select
                  label="Carrera"
                  placeholder="Seleccioná una carrera"
                  options={carreraOptions}
                  error={errors.carrera_id?.message}
                  {...register('carrera_id')}
                />
                <Select
                  label="Cohorte"
                  placeholder={carreraId ? 'Seleccioná un cohorte' : 'Primero seleccioná una carrera'}
                  options={cohorteOptions}
                  error={errors.cohorte_id?.message}
                  disabled={!carreraId}
                  {...register('cohorte_id')}
                />
              </>
            )}

            {step === 2 && (
              <>
                <h2 className="text-lg font-semibold">Seleccionar Rol y Docentes</h2>
                <Select
                  label="Rol"
                  placeholder="Seleccioná un rol"
                  options={rolOptions}
                  error={errors.rol_id?.message}
                  {...register('rol_id')}
                />

                <div className="space-y-2">
                  <label className="mb-1 block text-sm font-medium text-secondary-700">
                    Buscar docentes
                  </label>
                  <input
                    type="text"
                    className="block w-full rounded-lg border border-secondary-300 px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-secondary-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1"
                    placeholder="Escribí al menos 2 caracteres para buscar..."
                    value={userQuery}
                    onChange={(e) => setUserQuery(e.target.value)}
                  />
                  {searching && (
                    <div className="flex justify-center py-2">
                      <Spinner size="sm" />
                    </div>
                  )}
                  {userQuery.length >= 2 && !searching && searchResults.length === 0 && (
                    <p className="text-sm text-secondary-500">Sin resultados</p>
                  )}
                  {searchResults.length > 0 && (
                    <div className="max-h-48 space-y-1 overflow-y-auto rounded-lg border border-secondary-200 p-2">
                      {searchResults.map((user) => {
                        const checked = usuarioIds.includes(user.id);
                        return (
                          <label
                            key={user.id}
                            className={clsx(
                              'flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors',
                              checked
                                ? 'bg-primary-50 text-primary-800'
                                : 'hover:bg-secondary-50'
                            )}
                          >
                            <input
                              type="checkbox"
                              className="h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
                              checked={checked}
                              onChange={() => toggleUser(user)}
                            />
                            {user.nombre} {user.apellidos}
                            {user.legajo && (
                              <span className="text-secondary-400">({user.legajo})</span>
                            )}
                          </label>
                        );
                      })}
                    </div>
                  )}

                  {selectedUsers.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {selectedUsers.map((u) => (
                        <span
                          key={u.id}
                          className="inline-flex items-center gap-1 rounded-full bg-primary-100 px-2.5 py-0.5 text-xs font-medium text-primary-700"
                        >
                          {u.nombre} {u.apellidos}
                          <button
                            type="button"
                            className="ml-1 text-primary-500 hover:text-primary-700"
                            onClick={() => toggleUser(u)}
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                  {errors.usuario_ids && (
                    <p className="mt-1 text-sm text-danger-600" role="alert">
                      {errors.usuario_ids.message}
                    </p>
                  )}
                </div>
              </>
            )}

            {step === 3 && (
              <>
                <h2 className="text-lg font-semibold">Definir Vigencia y Comisiones</h2>
                <Input
                  label="Vigencia Desde"
                  type="date"
                  error={errors.vig_desde?.message}
                  {...register('vig_desde')}
                />
                <Input
                  label="Vigencia Hasta"
                  type="date"
                  {...register('vig_hasta')}
                />
                <Input
                  label="Comisiones (opcional)"
                  placeholder="Ej: A, B, C"
                  {...register('comisiones')}
                />
              </>
            )}

            {step === 4 && (
              <>
                <h2 className="text-lg font-semibold">Confirmar Asignación</h2>
                <div className="space-y-2 rounded-lg bg-secondary-50 p-4 text-sm">
                  <p>
                    <strong>Materia:</strong>{' '}
                    {resolvedMateria?.nombre ?? materiaId}
                  </p>
                  <p>
                    <strong>Carrera:</strong>{' '}
                    {resolvedCarrera ? `${resolvedCarrera.codigo} — ${resolvedCarrera.nombre}` : carreraId}
                  </p>
                  <p>
                    <strong>Cohorte:</strong>{' '}
                    {resolvedCohorte?.nombre ?? cohorteId}
                  </p>
                  <p>
                    <strong>Rol:</strong>{' '}
                    {resolvedRol?.nombre ?? rolId}
                  </p>
                  <p>
                    <strong>Docentes seleccionados:</strong>{' '}
                    {selectedUsers.length > 0
                      ? selectedUsers.map((u) => `${u.nombre} ${u.apellidos}`).join(', ')
                      : usuarioIds.join(', ')}
                  </p>
                  <p>
                    <strong>Vigencia:</strong> {vigDesde}
                    {vigHasta ? ` → ${vigHasta}` : ' (sin fecha de fin)'}
                  </p>
                </div>
              </>
            )}

            <div className="flex justify-between">
              <Button variant="secondary" type="button" onClick={handlePrev} disabled={step === 1}>
                Anterior
              </Button>
              {step < TOTAL_STEPS ? (
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
