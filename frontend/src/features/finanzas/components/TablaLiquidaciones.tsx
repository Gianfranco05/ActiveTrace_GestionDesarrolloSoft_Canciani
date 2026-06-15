import { useState } from 'react';

import { DataTable } from '@/shared/components/ui/DataTable';

import type { Liquidacion } from '@/features/finanzas/types/liquidacion.types';
import type { Column } from '@/shared/components/ui/DataTable';

type TabType = 'general' | 'nexo' | 'factura';

interface TablaLiquidacionesProps {
  liquidaciones: Liquidacion[];
  isLoading: boolean;
}

const tabs: { key: TabType; label: string }[] = [
  { key: 'general', label: 'General' },
  { key: 'nexo', label: 'NEXO' },
  { key: 'factura', label: 'Factura' },
];

export function TablaLiquidaciones({ liquidaciones, isLoading }: TablaLiquidacionesProps) {
  const [activeTab, setActiveTab] = useState<TabType>('general');

  const filtered = liquidaciones.filter((l) => {
    if (activeTab === 'nexo') return l.es_nexo;
    if (activeTab === 'factura') return l.excluido_por_factura;
    return true;
  });

  const columns: Column[] = [
    { key: 'docente_nombre', header: 'Docente' },
    { key: 'rol', header: 'Rol' },
    { key: 'comisiones', header: 'Comisiones' },
    {
      key: 'monto_base', header: 'Monto Base',
      render: (item) => (item.monto_base as number).toLocaleString('es-AR', { style: 'currency', currency: 'ARS' }),
    },
    {
      key: 'monto_plus', header: 'Monto Plus',
      render: (item) => (item.monto_plus as number).toLocaleString('es-AR', { style: 'currency', currency: 'ARS' }),
    },
    {
      key: 'total', header: 'Total',
      render: (item) => (item.total as number).toLocaleString('es-AR', { style: 'currency', currency: 'ARS' }),
      className: 'font-semibold',
    },
  ];

  return (
    <div>
      <div className="mb-4 flex gap-2 border-b border-secondary-200">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'border-b-2 border-primary-600 text-primary-700'
                : 'text-secondary-500 hover:text-secondary-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <DataTable
        columns={columns}
        data={filtered}
        keyExtractor={(item) => item.id as string}
        emptyMessage="No hay liquidaciones para este periodo"
        isLoading={isLoading}
      />
    </div>
  );
}
