import { Spinner } from '@/shared/components/ui/Spinner';

import type { LiquidacionKPI } from '@/features/finanzas/types/liquidacion.types';

interface KPILiquidacionesProps {
  kpi?: LiquidacionKPI;
  isLoading: boolean;
}

export function KPILiquidaciones({ kpi, isLoading }: KPILiquidacionesProps) {
  if (isLoading) {
    return (
      <div className="flex justify-center py-4">
        <Spinner size="md" />
      </div>
    );
  }

  if (!kpi) return null;

  const cards = [
    { label: 'Total General', value: kpi.total_general.toLocaleString('es-AR', { style: 'currency', currency: 'ARS' }), color: 'bg-primary-50 text-primary-700 border-primary-200' },
    { label: 'Total NEXO', value: kpi.total_nexo.toLocaleString('es-AR', { style: 'currency', currency: 'ARS' }), color: 'bg-amber-50 text-amber-700 border-amber-200' },
    { label: 'Total sin Factura', value: kpi.total_sin_factura.toLocaleString('es-AR', { style: 'currency', currency: 'ARS' }), color: 'bg-green-50 text-green-700 border-green-200' },
    { label: 'Docentes', value: `${kpi.total_docentes} (${kpi.total_facturantes} fact.)`, color: 'bg-blue-50 text-blue-700 border-blue-200' },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`rounded-lg border p-4 ${card.color}`}
        >
          <p className="text-sm font-medium opacity-75">{card.label}</p>
          <p className="mt-1 text-2xl font-bold">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
