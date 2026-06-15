import { useQuery } from '@tanstack/react-query';

import { Select } from '@/shared/components/ui/Select';
import { Spinner } from '@/shared/components/ui/Spinner';
import api from '@/shared/services/api';

interface Materia {
  id: string;
  nombre: string;
  comision: string;
}

interface MateriaSelectorProps {
  value: string;
  onChange: (materiaId: string) => void;
  disabled?: boolean;
}

export function MateriaSelector({ value, onChange, disabled }: MateriaSelectorProps) {
  const { data: materias, isLoading, error } = useQuery<Materia[]>({
    queryKey: ['materias-asignadas'],
    queryFn: async () => {
      const { data } = await api.get('/equipos/mis-materias');
      return data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-2">
        <Spinner size="sm" />
        <span className="text-sm text-secondary-500">Cargando materias...</span>
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-sm text-danger-600">Error al cargar materias</p>
    );
  }

  const options = [
    { value: '', label: '— Todas las materias —' },
    ...(materias ?? []).map((m) => ({
      value: m.id,
      label: `${m.nombre} — ${m.comision}`,
    })),
  ];

  return (
    <Select
      label="Materia"
      placeholder="Seleccioná una materia"
      options={options}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
    />
  );
}
