import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';

interface FiltrosMonitorProps {
  filtros: Record<string, string>;
  onChange: (key: string, value: string) => void;
  onLimpiar: () => void;
  showDateFilters: boolean;
}

export function FiltrosMonitor({ filtros, onChange, onLimpiar, showDateFilters }: FiltrosMonitorProps) {
  return (
    <div className="rounded-lg border border-secondary-200 bg-white p-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Input
          label="Alumno"
          placeholder="Buscar por nombre..."
          value={filtros.alumno ?? ''}
          onChange={(e) => onChange('alumno', e.target.value)}
        />
        <Input
          label="Correo"
          placeholder="Buscar por correo..."
          value={filtros.correo ?? ''}
          onChange={(e) => onChange('correo', e.target.value)}
        />
        <Input
          label="Comisión"
          placeholder="Filtrar por comisión..."
          value={filtros.comision ?? ''}
          onChange={(e) => onChange('comision', e.target.value)}
        />
        <Input
          label="Regional"
          placeholder="Filtrar por regional..."
          value={filtros.regional ?? ''}
          onChange={(e) => onChange('regional', e.target.value)}
        />
        <Input
          label="Actividad"
          placeholder="Filtrar por actividad..."
          value={filtros.actividad ?? ''}
          onChange={(e) => onChange('actividad', e.target.value)}
        />
        <Input
          label="Mín. actividades"
          type="number"
          min={0}
          placeholder="0"
          value={filtros.minActividades ?? ''}
          onChange={(e) => onChange('minActividades', e.target.value)}
        />
        {showDateFilters && (
          <>
            <Input
              label="Fecha desde"
              type="date"
              value={filtros.fechaDesde ?? ''}
              onChange={(e) => onChange('fechaDesde', e.target.value)}
            />
            <Input
              label="Fecha hasta"
              type="date"
              value={filtros.fechaHasta ?? ''}
              onChange={(e) => onChange('fechaHasta', e.target.value)}
            />
          </>
        )}
      </div>
      <div className="mt-4">
        <Button variant="secondary" size="sm" onClick={onLimpiar}>
          Limpiar filtros
        </Button>
      </div>
    </div>
  );
}
