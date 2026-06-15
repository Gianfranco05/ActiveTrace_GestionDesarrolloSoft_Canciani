import { Select } from '@/shared/components/ui/Select';

const MESES = [
  { value: '01', label: 'Enero' },
  { value: '02', label: 'Febrero' },
  { value: '03', label: 'Marzo' },
  { value: '04', label: 'Abril' },
  { value: '05', label: 'Mayo' },
  { value: '06', label: 'Junio' },
  { value: '07', label: 'Julio' },
  { value: '08', label: 'Agosto' },
  { value: '09', label: 'Septiembre' },
  { value: '10', label: 'Octubre' },
  { value: '11', label: 'Noviembre' },
  { value: '12', label: 'Diciembre' },
];

interface FiltrosLiquidacionProps {
  cohortes: { value: string; label: string }[];
  cohorteId: string;
  mes: string;
  onCohorteChange: (value: string) => void;
  onMesChange: (value: string) => void;
}

export function FiltrosLiquidacion({
  cohortes,
  cohorteId,
  mes,
  onCohorteChange,
  onMesChange,
}: FiltrosLiquidacionProps) {
  return (
    <div className="flex flex-wrap gap-4">
      <div className="w-64">
        <Select
          label="Cohorte"
          options={cohortes}
          placeholder="Todas las cohortes"
          value={cohorteId}
          onChange={(e) => onCohorteChange(e.target.value)}
        />
      </div>
      <div className="w-48">
        <Select
          label="Mes"
          options={MESES}
          placeholder="Todos los meses"
          value={mes}
          onChange={(e) => onMesChange(e.target.value)}
        />
      </div>
    </div>
  );
}
