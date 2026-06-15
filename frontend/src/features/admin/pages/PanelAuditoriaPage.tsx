import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';

import { AccionesPorDia } from '@/features/admin/components/AccionesPorDia';
import { AuditoriaGlobalFilter } from '@/features/admin/components/AuditoriaGlobalFilter';
import { EstadoComunicaciones } from '@/features/admin/components/EstadoComunicaciones';
import { InteraccionesDocente } from '@/features/admin/components/InteraccionesDocente';
import { UltimasAcciones } from '@/features/admin/components/UltimasAcciones';
import { useMetricasAuditoria } from '@/features/admin/hooks/useAuditoria';
import { Button } from '@/shared/components/ui/Button';

import type { AuditoriaFilter } from '@/features/admin/types/auditoria.types';

export function PanelAuditoriaPage() {
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [materiaId, setMateriaId] = useState('');

  const filter = useMemo<AuditoriaFilter>(
    () => ({
      fecha_desde: fechaDesde || undefined,
      fecha_hasta: fechaHasta || undefined,
      materia_id: materiaId || undefined,
    }),
    [fechaDesde, fechaHasta, materiaId]
  );

  const {
    accionesPorDia,
    estadoComunicaciones,
    interaccionesDocente,
    ultimasAcciones,
  } = useMetricasAuditoria(filter);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Panel de Auditoría</h1>
          <p className="mt-1 text-sm text-secondary-500">Métricas de actividad del sistema</p>
        </div>
        <Link to="/admin/auditoria/log">
          <Button variant="secondary" size="sm">Ver Log Completo</Button>
        </Link>
      </div>

      <AuditoriaGlobalFilter
        fechaDesde={fechaDesde}
        fechaHasta={fechaHasta}
        materiaId={materiaId}
        onFechaDesdeChange={setFechaDesde}
        onFechaHastaChange={setFechaHasta}
        onMateriaIdChange={setMateriaId}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-secondary-200 bg-white p-4">
          <AccionesPorDia
            data={accionesPorDia.data ?? []}
            isLoading={accionesPorDia.isLoading}
          />
        </div>
        <div className="rounded-lg border border-secondary-200 bg-white p-4">
          <EstadoComunicaciones
            data={estadoComunicaciones.data ?? []}
            isLoading={estadoComunicaciones.isLoading}
          />
        </div>
        <div className="rounded-lg border border-secondary-200 bg-white p-4 lg:col-span-2">
          <InteraccionesDocente
            data={interaccionesDocente.data ?? []}
            isLoading={interaccionesDocente.isLoading}
          />
        </div>
      </div>

      <div className="rounded-lg border border-secondary-200 bg-white p-4">
        <UltimasAcciones
          data={ultimasAcciones.data ?? []}
          isLoading={ultimasAcciones.isLoading}
        />
      </div>
    </div>
  );
}
