import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod/v4';

import { useCrearTarea } from '@/features/coordinacion/tareas/hooks/useTareas';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Select } from '@/shared/components/ui/Select';
import { Textarea } from '@/shared/components/ui/Textarea';
import api from '@/shared/services/api';

const tareaSchema = z.object({
  titulo: z.string().min(1, 'El título es obligatorio'),
  descripcion: z.string().optional(),
  materia_id: z.string().min(1, 'Seleccioná una materia'),
  docente_asignado_id: z.string().min(1, 'Seleccioná un docente'),
  criterio_cierre: z.string().optional(),
});

type TareaFormValues = z.infer<typeof tareaSchema>;

export function TareaFormPage() {
  const navigate = useNavigate();
  const { mutateAsync, isPending } = useCrearTarea();

  // Fetch materias y usuarios para los dropdowns
  const { data: materias = [] } = useQuery<{ id: string; nombre: string; codigo: string }[]>({
    queryKey: ['materias-tarea'],
    queryFn: async () => {
      const { data } = await api.get<{ items: { id: string; nombre: string; codigo: string }[] }>('/v1/estructura/materias');
      return data.items ?? [];
    },
  });

  const { data: usuarios = [] } = useQuery<{ id: string; nombre: string; apellidos: string }[]>({
    queryKey: ['usuarios-tarea'],
    queryFn: async () => {
      const { data } = await api.get<{ items: { id: string; nombre: string; apellidos: string }[] }>('/v1/admin/usuarios', { params: { rol: 'PROFESOR' } });
      return data.items ?? [];
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TareaFormValues>({
    resolver: zodResolver(tareaSchema),
    defaultValues: {
      titulo: '',
      descripcion: '',
      materia_id: '',
      docente_asignado_id: '',
      criterio_cierre: '',
    },
  });

  const onSubmit = async (values: TareaFormValues) => {
    await mutateAsync({
      titulo: values.titulo,
      descripcion: values.descripcion ?? '',
      materia_id: values.materia_id,
      docente_asignado_id: values.docente_asignado_id,
      criterio_cierre: values.criterio_cierre ?? '',
    });
    navigate('/coordinacion/tareas');
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-secondary-900">Nueva Tarea</h1>

      <Card>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input label="Título" error={errors.titulo?.message} {...register('titulo')} />
          <Textarea label="Descripción" rows={4} {...register('descripcion')} />

          <Select
            label="Materia"
            placeholder="Seleccioná una materia"
            options={materias.map((m) => ({ value: m.id, label: `${m.codigo} — ${m.nombre}` }))}
            error={errors.materia_id?.message}
            {...register('materia_id')}
          />

          <Select
            label="Docente asignado"
            placeholder="Seleccioná un docente"
            options={usuarios.map((u) => ({ value: u.id, label: `${u.nombre} ${u.apellidos}` }))}
            error={errors.docente_asignado_id?.message}
            {...register('docente_asignado_id')}
          />

          <Textarea label="Criterio de Cierre" rows={3} {...register('criterio_cierre')} />

          <div className="flex justify-end gap-2">
            <Button variant="secondary" type="button" onClick={() => navigate('/coordinacion/tareas')}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={isPending}>Crear Tarea</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
