import { Input } from '@/shared/components/ui/Input';

interface AuditoriaGlobalFilterProps {
  fechaDesde: string;
  fechaHasta: string;
  materiaId: string;
  onFechaDesdeChange: (value: string) => void;
  onFechaHastaChange: (value: string) => void;
  onMateriaIdChange: (value: string) => void;
}

export function AuditoriaGlobalFilter({
  fechaDesde,
  fechaHasta,
  materiaId,
  onFechaDesdeChange,
  onFechaHastaChange,
  onMateriaIdChange,
}: AuditoriaGlobalFilterProps) {
  return (
    <div className="flex flex-wrap gap-4 rounded-lg border border-secondary-200 bg-white p-4">
      <div className="w-44">
        <Input
          label="Fecha desde"
          type="date"
          value={fechaDesde}
          onChange={(e) => onFechaDesdeChange(e.target.value)}
        />
      </div>
      <div className="w-44">
        <Input
          label="Fecha hasta"
          type="date"
          value={fechaHasta}
          onChange={(e) => onFechaHastaChange(e.target.value)}
        />
      </div>
      <div className="w-48">
        <Input
          label="ID Materia"
          placeholder="Filtrar por materia..."
          value={materiaId}
          onChange={(e) => onMateriaIdChange(e.target.value)}
        />
      </div>
    </div>
  );
}
