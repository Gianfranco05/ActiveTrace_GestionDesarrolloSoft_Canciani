import { useMemo, useState } from 'react';

import { useMonitorGeneral, useMonitorDocente } from '@/features/coordinacion/monitores/hooks/useMonitores';
import { exportarMonitores } from '@/features/coordinacion/monitores/services/monitores.service';
import { Button } from '@/shared/components/ui/Button';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { Input } from '@/shared/components/ui/Input';
import { Pagination } from '@/shared/components/ui/Pagination';
import { Spinner } from '@/shared/components/ui/Spinner';
import { Tabs } from '@/shared/components/ui/Tabs';

import type { MonitorGeneralFilters, MonitorDocenteFilters } from '@/features/coordinacion/monitores/types/monitores.types';

const defaultFilters: MonitorGeneralFilters = {
  materia_id: undefined,
  regional: undefined,
  comision: undefined,
  busqueda: undefined,
  estado: undefined,
  criterio: undefined,
};

export function MonitoresPage() {
  const [activeTab, setActiveTab] = useState('general');
  const [generalPage, setGeneralPage] = useState(1);
  const [docentePage, setDocentePage] = useState(1);
  const [generalFilters, setGeneralFilters] = useState<MonitorGeneralFilters>(defaultFilters);
  const [docenteFilters, setDocenteFilters] = useState<MonitorDocenteFilters>(defaultFilters);

  const { data: generalData, isLoading: loadingGeneral } = useMonitorGeneral(generalPage, generalFilters);
  const { data: docenteData, isLoading: loadingDocente } = useMonitorDocente(docentePage, docenteFilters);

  const generalColumns = useMemo<Column[]>(
    () => [
      { key: 'alumno_nombre', header: 'Alumno' },
      { key: 'materia_nombre', header: 'Materia' },
      { key: 'comision', header: 'Comisión' },
      { key: 'regional', header: 'Regional' },
      { key: 'estado', header: 'Estado' },
      { key: 'criterio', header: 'Criterio' },
      { key: 'actividades_cumplidas', header: 'Actividades' },
    ],
    []
  );

  const docenteColumns = useMemo<Column[]>(
    () => [
      { key: 'alumno_nombre', header: 'Alumno' },
      { key: 'docente_nombre', header: 'Docente' },
      { key: 'materia_nombre', header: 'Materia' },
      { key: 'comision', header: 'Comisión' },
      { key: 'regional', header: 'Regional' },
      { key: 'correo', header: 'Correo' },
      { key: 'actividades_cumplidas', header: 'Actividades' },
    ],
    []
  );

  const tabs = [
    {
      id: 'general',
      label: 'General',
      content: (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Input label="Materia" value={generalFilters.materia_id ?? ''} onChange={(e) => setGeneralFilters((f) => ({ ...f, materia_id: e.target.value || undefined }))} />
            <Input label="Regional" value={generalFilters.regional ?? ''} onChange={(e) => setGeneralFilters((f) => ({ ...f, regional: e.target.value || undefined }))} />
            <Input label="Comisión" value={generalFilters.comision ?? ''} onChange={(e) => setGeneralFilters((f) => ({ ...f, comision: e.target.value || undefined }))} />
            <Input label="Búsqueda" value={generalFilters.busqueda ?? ''} onChange={(e) => setGeneralFilters((f) => ({ ...f, busqueda: e.target.value || undefined }))} />
            <Input label="Estado" value={generalFilters.estado ?? ''} onChange={(e) => setGeneralFilters((f) => ({ ...f, estado: e.target.value || undefined }))} />
            <Input label="Criterio" value={generalFilters.criterio ?? ''} onChange={(e) => setGeneralFilters((f) => ({ ...f, criterio: e.target.value || undefined }))} />
          </div>
          <div className="flex justify-between">
            <Button variant="secondary" size="sm" onClick={() => { setGeneralFilters(defaultFilters); setGeneralPage(1); }}>
              Limpiar filtros
            </Button>
            <Button variant="secondary" size="sm" onClick={async () => {
              const blob = await exportarMonitores('general', generalFilters);
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = 'monitor-general.csv';
              a.click();
              URL.revokeObjectURL(url);
            }}>
              Exportar
            </Button>
          </div>
          {loadingGeneral ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : (
            <>
              <DataTable columns={generalColumns} data={generalData?.data ?? []} keyExtractor={(r) => r.id} />
              {generalData && <Pagination page={generalData.page} totalPages={generalData.total_pages} onPageChange={setGeneralPage} />}
            </>
          )}
        </div>
      ),
    },
    {
      id: 'seguimiento',
      label: 'Seguimiento por docente',
      content: (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Input label="Materia" value={docenteFilters.materia_id ?? ''} onChange={(e) => setDocenteFilters((f) => ({ ...f, materia_id: e.target.value || undefined }))} />
            <Input label="Docente" value={docenteFilters.docente_id ?? ''} onChange={(e) => setDocenteFilters((f) => ({ ...f, docente_id: e.target.value || undefined }))} />
            <Input label="Regional" value={docenteFilters.regional ?? ''} onChange={(e) => setDocenteFilters((f) => ({ ...f, regional: e.target.value || undefined }))} />
            <Input label="Fecha Desde" type="date" value={docenteFilters.fecha_desde ?? ''} onChange={(e) => setDocenteFilters((f) => ({ ...f, fecha_desde: e.target.value || undefined }))} />
            <Input label="Fecha Hasta" type="date" value={docenteFilters.fecha_hasta ?? ''} onChange={(e) => setDocenteFilters((f) => ({ ...f, fecha_hasta: e.target.value || undefined }))} />
            <Input label="Min. Actividades" type="number" value={docenteFilters.minimo_actividades ?? ''} onChange={(e) => setDocenteFilters((f) => ({ ...f, minimo_actividades: e.target.value ? Number(e.target.value) : undefined }))} />
          </div>
          <div className="flex justify-between">
            <Button variant="secondary" size="sm" onClick={() => { setDocenteFilters(defaultFilters); setDocentePage(1); }}>
              Limpiar filtros
            </Button>
            <Button variant="secondary" size="sm" onClick={async () => {
              const blob = await exportarMonitores('seguimiento', docenteFilters);
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = 'monitor-seguimiento.csv';
              a.click();
              URL.revokeObjectURL(url);
            }}>
              Exportar
            </Button>
          </div>
          {loadingDocente ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : (
            <>
              <DataTable columns={docenteColumns} data={docenteData?.data ?? []} keyExtractor={(r) => r.id} />
              {docenteData && <Pagination page={docenteData.page} totalPages={docenteData.total_pages} onPageChange={setDocentePage} />}
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-secondary-900">Monitores</h1>
      <Tabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
}
