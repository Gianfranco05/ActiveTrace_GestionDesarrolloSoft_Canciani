import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { useMisEquipos, useModificarVigencia, useMisMaterias } from '@/features/coordinacion/equipos/hooks/useEquipos';
import { exportarEquipo } from '@/features/coordinacion/equipos/services/equipos.service';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { Input } from '@/shared/components/ui/Input';
import { Modal } from '@/shared/components/ui/Modal';
import { Select } from '@/shared/components/ui/Select';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';
import api from '@/shared/services/api';

import type { AsignacionResponse, EquiposFilters } from '@/features/coordinacion/equipos/types/equipos.types';

interface CarreraItem {
  id: string;
  codigo: string;
  nombre: string;
}

interface CohorteItem {
  id: string;
  nombre: string;
}

const ESTADO_LABEL: Record<string, string> = {
  Vigente: 'Activa',
  Vencida: 'Inactiva',
  Futuro: 'Pendiente',
};

function estadoVariant(v: string): 'active' | 'inactive' | 'pending' {
  if (v === 'Vigente') return 'active';
  if (v === 'Vencida') return 'inactive';
  return 'pending';
}

export function EquiposPage() {
  const [filters, setFilters] = useState<EquiposFilters>({});
  const { data: equiposData, isLoading } = useMisEquipos(filters);
  const [vigenciaModal, setVigenciaModal] = useState<AsignacionResponse | null>(null);
  const [vigDesde, setVigDesde] = useState('');
  const [vigHasta, setVigHasta] = useState('');
  const modificarVigencia = useModificarVigencia();

  const { data: materias = [] } = useMisMaterias();

  const { data: carreras = [] } = useQuery<CarreraItem[]>({
    queryKey: ['carreras-equipos'],
    queryFn: async () => {
      const { data } = await api.get<{ items: CarreraItem[] }>('/v1/estructura/carreras');
      return data.items ?? [];
    },
  });

  const { data: cohortes = [] } = useQuery<CohorteItem[]>({
    queryKey: ['cohortes-equipos'],
    queryFn: async () => {
      const { data } = await api.get<{ items: CohorteItem[] }>('/v1/estructura/cohortes');
      return data.items ?? [];
    },
  });

  const materiaOptions = useMemo(
    () => [{ value: '', label: 'Todas' }, ...materias.map((m) => ({ value: m.id, label: m.nombre }))],
    [materias]
  );

  const carreraOptions = useMemo(
    () => [{ value: '', label: 'Todas' }, ...carreras.map((c) => ({ value: c.id, label: `${c.codigo} — ${c.nombre}` }))],
    [carreras]
  );

  const enrichedItems = useMemo(() => {
    const items = equiposData?.items ?? [];
    return items
      .filter((a) => a.materia_id || a.carrera_id || a.cohorte_id)
      .map((a) => {
        const materia = materias.find((m) => m.id === a.materia_id);
        const carrera = carreras.find((c) => c.id === a.carrera_id);
        const cohorte = cohortes.find((c) => c.id === a.cohorte_id);
        return {
          ...a,
          _materia: materia?.nombre ?? a.materia_id ?? '—',
          _carrera: carrera ? `${carrera.codigo} — ${carrera.nombre}` : a.carrera_id ?? '—',
          _cohorte: cohorte?.nombre ?? a.cohorte_id ?? '—',
          _rol: a.rol_nombre ?? '—',
        };
      });
  }, [equiposData, materias, carreras, cohortes]);

  const columns = useMemo<Column[]>(
    () => [
      { key: '_materia' as keyof typeof enrichedItems[number], header: 'Materia' },
      { key: '_carrera' as keyof typeof enrichedItems[number], header: 'Carrera' },
      { key: '_cohorte' as keyof typeof enrichedItems[number], header: 'Cohorte' },
      { key: '_rol' as keyof typeof enrichedItems[number], header: 'Rol' },
      {
        key: 'estado_vigencia' as keyof typeof enrichedItems[number],
        header: 'Estado',
        render: (item: any) => (
          <StatusBadge
            variant={estadoVariant(item.estado_vigencia)}
            label={ESTADO_LABEL[item.estado_vigencia] ?? item.estado_vigencia}
          />
        ),
      },
      {
        key: 'vig_desde' as keyof typeof enrichedItems[number],
        header: 'Vigencia Desde',
      },
      {
        key: 'vig_hasta' as keyof typeof enrichedItems[number],
        header: 'Vigencia Hasta',
        render: (item) => <span>{item.vig_hasta ?? '—'}</span>,
      },
      {
        key: 'acciones' as keyof typeof enrichedItems[number],
        header: 'Acciones',
        render: (item: any) => (
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="ghost"
              aria-label="Modificar vigencia"
              onClick={(e) => {
                e.stopPropagation();
                setVigenciaModal(item);
                setVigDesde(item.vig_desde);
                setVigHasta(item.vig_hasta ?? '');
              }}
            >
              Vigencia
            </Button>
            <Button
              size="sm"
              variant="ghost"
              aria-label="Exportar equipo"
              onClick={async (e) => {
                e.stopPropagation();
                if (!item.materia_id || !item.carrera_id || !item.cohorte_id) return;
                try {
                  const blob = await exportarEquipo(item.materia_id, item.carrera_id, item.cohorte_id);
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `equipo-${item.materia_id}.csv`;
                  a.click();
                  URL.revokeObjectURL(url);
                } catch {
                  toast.error('Error al exportar el equipo');
                }
              }}
            >
              Exportar
            </Button>
          </div>
        ),
      },
    ],
    []
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-secondary-900">Mis Equipos</h1>
        <div className="flex gap-2">
          <Link to="/coordinacion/equipos/asignaciones">
            <Button variant="secondary" size="sm">
              Asignaciones
            </Button>
          </Link>
          <Link to="/coordinacion/equipos/asignacion-masiva">
            <Button variant="secondary" size="sm">
              Asignación Masiva
            </Button>
          </Link>
          <Link to="/coordinacion/equipos/clonar">
            <Button variant="secondary" size="sm">
              Clonar Equipo
            </Button>
          </Link>
        </div>
      </div>

      <Card>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Select
              label="Estado"
              options={[
                { value: '', label: 'Todas' },
                { value: 'Vigente', label: 'Activa' },
                { value: 'Vencida', label: 'Inactiva' },
                { value: 'Futuro', label: 'Pendiente' },
              ]}
            value={filters.estado ?? ''}
            onChange={(e) =>
              setFilters((f) => ({ ...f, estado: e.target.value || undefined }))
            }
          />
          <Select
            label="Materia"
            options={materiaOptions}
            value={filters.materia_id ?? ''}
            onChange={(e) =>
              setFilters((f) => ({ ...f, materia_id: e.target.value || undefined }))
            }
          />
          <Select
            label="Carrera"
            options={carreraOptions}
            value={filters.carrera_id ?? ''}
            onChange={(e) =>
              setFilters((f) => ({ ...f, carrera_id: e.target.value || undefined }))
            }
          />
        </div>
      </Card>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : enrichedItems.length > 0 ? (
        <Card>
          <DataTable columns={columns} data={enrichedItems} keyExtractor={(e) => e.id} />
        </Card>
      ) : (
        <Card>
          <div className="py-12 text-center">
            <p className="text-secondary-500">No tenés equipos asignados</p>
            <Link to="/coordinacion/equipos/asignacion-masiva">
              <Button variant="primary" className="mt-4">
                Crear asignación
              </Button>
            </Link>
          </div>
        </Card>
      )}

      <Modal
        isOpen={!!vigenciaModal}
        onClose={() => setVigenciaModal(null)}
        title="Modificar Vigencia"
      >
        <div className="space-y-4">
          <Input
            label="Vigencia Desde"
            type="date"
            value={vigDesde}
            onChange={(e) => setVigDesde(e.target.value)}
          />
          <Input
            label="Vigencia Hasta"
            type="date"
            value={vigHasta}
            onChange={(e) => setVigHasta(e.target.value)}
          />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setVigenciaModal(null)}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              isLoading={modificarVigencia.isPending}
              onClick={async () => {
                if (!vigenciaModal) return;
                if (!vigenciaModal.materia_id || !vigenciaModal.carrera_id || !vigenciaModal.cohorte_id) {
                  toast.error('La asignación no tiene materia, carrera o cohorte');
                  return;
                }
                await modificarVigencia.mutateAsync({
                  materia_id: vigenciaModal.materia_id,
                  carrera_id: vigenciaModal.carrera_id,
                  cohorte_id: vigenciaModal.cohorte_id,
                  vig_desde: vigDesde,
                  vig_hasta: vigHasta || null,
                });
                setVigenciaModal(null);
                toast.success('Vigencia actualizada correctamente');
              }}
            >
              Guardar
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
