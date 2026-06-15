import { useState } from 'react';

import { useReservas } from '@/features/coordinacion/coloquios/hooks/useColoquios';
import { Card } from '@/shared/components/ui/Card';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { Input } from '@/shared/components/ui/Input';
import { Spinner } from '@/shared/components/ui/Spinner';

import type { AgendaReservasFilters } from '@/features/coordinacion/coloquios/types/coloquios.types';

export function AgendaReservasPage() {
  const [filters, setFilters] = useState<AgendaReservasFilters>({});
  const { data: reservas, isLoading } = useReservas(filters);

  const columns: Column[] = [
    { key: 'alumno_nombre', header: 'Alumno' },
    { key: 'materia_nombre', header: 'Materia' },
    { key: 'convocatoria_nombre', header: 'Convocatoria' },
    { key: 'dia', header: 'Día' },
    { key: 'horario', header: 'Horario' },
    { key: 'estado', header: 'Estado' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-secondary-900">Agenda de Reservas</h1>

      <Card>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Input label="Materia" value={filters.materia_id ?? ''} onChange={(e) => setFilters((f) => ({ ...f, materia_id: e.target.value || undefined }))} />
          <Input label="Convocatoria" value={filters.convocatoria_id ?? ''} onChange={(e) => setFilters((f) => ({ ...f, convocatoria_id: e.target.value || undefined }))} />
          <Input label="Día" type="date" value={filters.dia ?? ''} onChange={(e) => setFilters((f) => ({ ...f, dia: e.target.value || undefined }))} />
        </div>
      </Card>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : (
        <Card>
          <DataTable columns={columns} data={reservas ?? []} keyExtractor={(r) => r.id} />
        </Card>
      )}
    </div>
  );
}
