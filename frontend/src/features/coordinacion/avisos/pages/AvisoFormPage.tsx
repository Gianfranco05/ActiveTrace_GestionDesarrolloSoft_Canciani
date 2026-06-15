import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod/v4';

import { useAviso, useCrearAviso, useEditarAviso } from '@/features/coordinacion/avisos/hooks/useAvisos';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Select } from '@/shared/components/ui/Select';
import { Spinner } from '@/shared/components/ui/Spinner';
import { Textarea } from '@/shared/components/ui/Textarea';
import api from '@/shared/services/api';

import type { AvisoFormData } from '@/features/coordinacion/avisos/types/avisos.types';

const ROLES_DISPONIBLES = ['ALUMNO', 'TUTOR', 'PROFESOR', 'COORDINADOR', 'NEXO', 'ADMIN', 'FINANZAS'] as const;

const PRIORIDADES = [
  { value: '0', label: 'Baja' },
  { value: '1', label: 'Media' },
  { value: '2', label: 'Alta' },
  { value: '3', label: 'Urgente' },
] as const;

const avisoSchema = z.object({
  titulo: z.string().min(1, 'El título es obligatorio'),
  cuerpo: z.string().min(1, 'El cuerpo es obligatorio'),
  alcance: z.enum(['Global', 'PorMateria', 'PorCohorte', 'PorRol']),
  rol_destino: z.string().optional(),
  severidad: z.enum(['Info', 'Advertencia', 'Critico']),
  inicio_en: z.string().min(1, 'La fecha de inicio es obligatoria'),
  fin_en: z.string().min(1, 'La fecha de fin es obligatoria'),
  orden: z.coerce.number().int().min(0),
  activo: z.boolean(),
  requiere_ack: z.boolean(),
  materia_id: z.string().optional(),
  cohorte_id: z.string().optional(),
});

type AvisoFormValues = z.infer<typeof avisoSchema>;

function toDatetimeLocal(dateStr: string | null | undefined): string {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toISOString().slice(0, 16);
}

export function AvisoFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = !!id;
  const { data: aviso, isLoading: loadingAviso } = useAviso(id ?? '');
  const { mutateAsync: crear, isPending: creating } = useCrearAviso();
  const { mutateAsync: editar, isPending: updating } = useEditarAviso();

  // Fetch materias y cohortes para los dropdowns
  const { data: materias = [] } = useQuery<{ id: string; nombre: string; codigo: string }[]>({
    queryKey: ['materias-dropdown'],
    queryFn: async () => {
      const { data } = await api.get<{ items: { id: string; nombre: string; codigo: string }[] }>('/v1/estructura/materias');
      return data.items ?? [];
    },
  });

  const { data: cohortes = [] } = useQuery<{ id: string; nombre: string }[]>({
    queryKey: ['cohortes-dropdown'],
    queryFn: async () => {
      const { data } = await api.get<{ items: { id: string; nombre: string }[] }>('/v1/estructura/cohortes');
      return data.items ?? [];
    },
  });

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<AvisoFormValues>({
    resolver: zodResolver(avisoSchema) as any,
    defaultValues: {
      titulo: '',
      cuerpo: '',
      alcance: 'Global',
      rol_destino: '',
      severidad: 'Info',
      inicio_en: '',
      fin_en: '',
      orden: 0,
      activo: true,
      requiere_ack: false,
    },
  });

  const alcance = watch('alcance');

  useEffect(() => {
    if (aviso) {
      reset({
        titulo: aviso.titulo,
        cuerpo: aviso.cuerpo,
        alcance: aviso.alcance as AvisoFormValues['alcance'],
        rol_destino: aviso.rol_destino ?? '',
        severidad: aviso.severidad as AvisoFormValues['severidad'],
        inicio_en: toDatetimeLocal(aviso.inicio_en),
        fin_en: toDatetimeLocal(aviso.fin_en),
        orden: aviso.orden,
        activo: aviso.activo,
        requiere_ack: aviso.requiere_ack,
        materia_id: aviso.materia_id ?? '',
        cohorte_id: aviso.cohorte_id ?? '',
      });
    }
  }, [aviso, reset]);

  if (isEditing && loadingAviso) {
    return <div className="flex justify-center py-12"><Spinner size="lg" /></div>;
  }

  const onSubmit = async (values: AvisoFormValues) => {
    const payload: AvisoFormData = {
      titulo: values.titulo,
      cuerpo: values.cuerpo,
      alcance: values.alcance,
      rol_destino: values.alcance === 'PorRol' ? values.rol_destino || null : null,
      severidad: values.severidad,
      inicio_en: new Date(values.inicio_en).toISOString(),
      fin_en: new Date(values.fin_en).toISOString(),
      orden: typeof values.orden === 'string' ? parseInt(values.orden, 10) : values.orden,
      activo: values.activo,
      requiere_ack: values.requiere_ack,
      materia_id: values.alcance === 'PorMateria' ? values.materia_id || undefined : undefined,
      cohorte_id: values.alcance === 'PorCohorte' ? values.cohorte_id || undefined : undefined,
    };

    try {
      if (isEditing) {
        await editar({ id: id!, payload });
      } else {
        await crear(payload);
      }
      navigate('/coordinacion/avisos');
    } catch (err: any) {
      console.error('Error:', err?.response?.data ?? err?.message ?? err);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-secondary-900">
        {isEditing ? 'Editar Aviso' : 'Nuevo Aviso'}
      </h1>

      <Card>
        <form onSubmit={handleSubmit(onSubmit as any)} className="space-y-4">
          <Input label="Título" error={errors.titulo?.message} {...register('titulo')} />
          <Textarea label="Cuerpo" rows={6} error={errors.cuerpo?.message} {...register('cuerpo')} />

          <Select
            label="Alcance"
            options={[
              { value: 'Global', label: 'Global' },
              { value: 'PorMateria', label: 'Por Materia' },
              { value: 'PorCohorte', label: 'Por Cohorte' },
              { value: 'PorRol', label: 'Por Rol' },
            ]}
            error={errors.alcance?.message}
            {...register('alcance')}
          />

          {alcance === 'PorMateria' && (
            <Select
              label="Materia"
              placeholder="Seleccioná una materia"
              options={materias.map((m) => ({ value: m.id, label: `${m.codigo} — ${m.nombre}` }))}
              {...register('materia_id')}
            />
          )}
          {alcance === 'PorCohorte' && (
            <Select
              label="Cohorte"
              placeholder="Seleccioná una cohorte"
              options={cohortes.map((c) => ({ value: c.id, label: c.nombre }))}
              {...register('cohorte_id')}
            />
          )}

          {alcance === 'PorRol' && (
            <Select
              label="Rol destinatario"
              options={ROLES_DISPONIBLES.map((r) => ({ value: r, label: r }))}
              {...register('rol_destino')}
            />
          )}

          <Select
            label="Severidad"
            options={[
              { value: 'Info', label: 'Info' },
              { value: 'Advertencia', label: 'Advertencia' },
              { value: 'Critico', label: 'Crítico' },
            ]}
            error={errors.severidad?.message}
            {...register('severidad')}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input label="Inicio" type="datetime-local" error={errors.inicio_en?.message} {...register('inicio_en')} />
            <Input label="Fin" type="datetime-local" error={errors.fin_en?.message} {...register('fin_en')} />
          </div>

          <Select
            label="Prioridad"
            options={PRIORIDADES.map((p) => ({ value: p.value, label: p.label }))}
            {...register('orden')}
          />

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input type="checkbox" {...register('activo')} />
              <span className="text-sm text-secondary-700">Activo</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" {...register('requiere_ack')} />
              <span className="text-sm text-secondary-700">Requiere confirmación</span>
            </label>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="secondary" type="button" onClick={() => navigate('/coordinacion/avisos')}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={creating || updating}>
              {isEditing ? 'Guardar Cambios' : 'Publicar'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
