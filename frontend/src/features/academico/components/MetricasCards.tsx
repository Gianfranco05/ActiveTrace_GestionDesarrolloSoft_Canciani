import { Card } from '@/shared/components/ui/Card';

import type { MetricaReporte } from '@/features/academico/types/analisis.types';

interface MetricasCardsProps {
  metricas: MetricaReporte;
  materiaId: string;
}

export function MetricasCards({ metricas, materiaId }: MetricasCardsProps) {
  const cards = [
    {
      label: 'Total Alumnos',
      value: metricas.total_alumnos,
      color: 'text-primary-600',
      link: `/academico/ranking?materiaId=${materiaId}`,
    },
    {
      label: 'Aprobados',
      value: `${metricas.alumnos_aprobados} / ${metricas.total_alumnos}`,
      color: 'text-green-600',
      link: `/academico/ranking?materiaId=${materiaId}`,
    },
    {
      label: '% Aprobación',
      value: `${Number(metricas.pct_aprobados).toFixed(0)}%`,
      color: Number(metricas.pct_aprobados) >= 60 ? 'text-green-600' : 'text-amber-600',
      link: `/academico/notas-finales?materiaId=${materiaId}`,
    },
    {
      label: 'Atrasados',
      value: metricas.alumnos_atrasados,
      color: metricas.alumnos_atrasados > 0 ? 'text-danger-600' : 'text-green-600',
      link: `/academico/atrasados?materiaId=${materiaId}`,
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <a key={card.label} href={card.link} className="block">
          <Card className="transition-shadow hover:shadow-lg">
            <p className="text-sm text-secondary-500">{card.label}</p>
            <p className={`mt-1 text-2xl font-bold ${card.color}`}>{card.value}</p>
          </Card>
        </a>
      ))}
    </div>
  );
}
