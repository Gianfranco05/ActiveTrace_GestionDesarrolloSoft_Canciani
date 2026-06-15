import { Input } from '@/shared/components/ui/Input';
import { Select } from '@/shared/components/ui/Select';
import { Card } from '@/shared/components/ui/Card';

const ROLES_OPTIONS = [
  { value: 'ADMIN', label: 'Admin' },
  { value: 'COORDINADOR', label: 'Coordinador' },
  { value: 'PROFESOR', label: 'Profesor' },
  { value: 'TUTOR', label: 'Tutor' },
  { value: 'NEXO', label: 'Nexo' },
  { value: 'FINANZAS', label: 'Finanzas' },
  { value: 'ALUMNO', label: 'Alumno' },
];

const ESTADOS = [
  { value: 'true', label: 'Activo' },
  { value: 'false', label: 'Inactivo' },
];

interface FiltrosUsuarioProps {
  rol: string;
  activo: string;
  busqueda: string;
  onRolChange: (value: string) => void;
  onActivoChange: (value: string) => void;
  onBusquedaChange: (value: string) => void;
}

export function FiltrosUsuario({
  rol,
  activo,
  busqueda,
  onRolChange,
  onActivoChange,
  onBusquedaChange,
}: FiltrosUsuarioProps) {
  return (
    <Card className="bg-secondary-50">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-secondary-500">Filtros de búsqueda</h3>
      <div className="flex flex-wrap items-end gap-4">
        <div className="w-48">
          <Select
            label="Rol"
            options={ROLES_OPTIONS}
            placeholder="Todos los roles"
            value={rol}
            onChange={(e) => onRolChange(e.target.value)}
          />
        </div>
        <div className="w-40">
          <Select
            label="Estado"
            options={ESTADOS}
            placeholder="Todos"
            value={activo}
            onChange={(e) => onActivoChange(e.target.value)}
          />
        </div>
        <div className="w-64">
          <Input
            label="Buscar"
            placeholder="Nombre o email..."
            value={busqueda}
            onChange={(e) => onBusquedaChange(e.target.value)}
          />
        </div>
      </div>
    </Card>
  );
}
