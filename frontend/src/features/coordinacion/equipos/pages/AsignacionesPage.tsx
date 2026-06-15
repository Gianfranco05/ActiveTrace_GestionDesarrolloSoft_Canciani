import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { useAsignaciones, useMisMaterias, useUpdateAsignacion } from '@/features/coordinacion/equipos/hooks/useEquipos';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { Input } from '@/shared/components/ui/Input';
import { Modal } from '@/shared/components/ui/Modal';
import { Pagination } from '@/shared/components/ui/Pagination';
import { Select } from '@/shared/components/ui/Select';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';
import api from '@/shared/services/api';

import type { AsignacionResponse, AsignacionesFilters } from '@/features/coordinacion/equipos/types/equipos.types';

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

interface CarreraItem { id: string; codigo: string; nombre: string; }
interface CohorteItem { id: string; nombre: string; }
interface RolItem { id: string; nombre: string; }

const PAGE_SIZE = 20;

export function AsignacionesPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<AsignacionesFilters>({});
  const { data: response, isLoading } = useAsignaciones(page, filters);
  const { mutateAsync: updateMutate, isPending: updating } = useUpdateAsignacion();
  const [editItem, setEditItem] = useState<AsignacionResponse | null>(null);
  const [editVigDesde, setEditVigDesde] = useState('');
  const [editVigHasta, setEditVigHasta] = useState('');
  const [editMateria, setEditMateria] = useState('');
  const [editCarrera, setEditCarrera] = useState('');
  const [editCohorte, setEditCohorte] = useState('');
  const [editRol, setEditRol] = useState('');

  const { data: materias = [] } = useMisMaterias();
  const { data: carreras = [] } = useQuery<CarreraItem[]>({
    queryKey: ['carreras-edi'],
    queryFn: async () => { const { data } = await api.get<{ items: CarreraItem[] }>('/v1/estructura/carreras'); return data.items ?? []; },
    staleTime: 300000,
  });
  const { data: cohortes = [] } = useQuery<CohorteItem[]>({
    queryKey: ['cohortes-edi'],
    queryFn: async () => { const { data } = await api.get<{ items: CohorteItem[] }>('/v1/estructura/cohortes'); return data.items ?? []; },
    staleTime: 300000,
  });
  const { data: roles = [] } = useQuery<RolItem[]>({
    queryKey: ['roles-edi'],
    queryFn: async () => { const { data } = await api.get<RolItem[]>('/v1/rbac/roles-names'); return data; },
    staleTime: 300000,
  });

  const rolOptions = useMemo(() => [{ value: '', label: 'Todos' }, ...roles.map((r) => ({ value: r.id, label: r.nombre }))], [roles]);

  const materiaOptions = useMemo(() => materias.map((m) => ({ value: m.id, label: m.nombre })), [materias]);
  const carreraOptions = useMemo(() => carreras.map((c) => ({ value: c.id, label: `${c.codigo} — ${c.nombre}` })), [carreras]);
  const cohorteOptions = useMemo(() => cohortes.map((c) => ({ value: c.id, label: c.nombre })), [cohortes]);
  const rolEditOptions = useMemo(() => roles.map((r) => ({ value: r.id, label: r.nombre })), [roles]);

  const enrichedItems = useMemo(() => {
    const items = response?.items ?? [];
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
          _usuario: a.usuario_id,
        };
      });
  }, [response, materias, carreras, cohortes]);

  const openEdit = (item: typeof enrichedItems[number]) => {
    setEditItem(item as AsignacionResponse);
    setEditVigDesde(item.vig_desde);
    setEditVigHasta(item.vig_hasta ?? '');
    setEditMateria(item.materia_id ?? '');
    setEditCarrera(item.carrera_id ?? '');
    setEditCohorte(item.cohorte_id ?? '');
    setEditRol(item.rol_id ?? '');
  };

  const handleUpdate = async () => {
    if (!editItem) return;
    try {
      const payload: Record<string, unknown> = {};
      if (editVigDesde) payload.vig_desde = editVigDesde;
      payload.vig_hasta = editVigHasta || null;
      if (editMateria) payload.materia_id = editMateria;
      if (editCarrera) payload.carrera_id = editCarrera;
      if (editCohorte) payload.cohorte_id = editCohorte;
      if (editRol) payload.rol_id = editRol;
      await updateMutate({ id: editItem.id, payload });
      setEditItem(null);
      toast.success('Asignación actualizada');
    } catch {
      toast.error('Error al actualizar');
    }
  };

  const totalPages = response ? Math.max(1, Math.ceil(response.total / PAGE_SIZE)) : 1;

  const columns: Column[] = useMemo(
    () => [
      { key: '_materia' as keyof typeof enrichedItems[number], header: 'Materia' },
      { key: '_carrera' as keyof typeof enrichedItems[number], header: 'Carrera' },
      { key: '_cohorte' as keyof typeof enrichedItems[number], header: 'Cohorte' },
      { key: '_rol' as keyof typeof enrichedItems[number], header: 'Rol' },
      { key: 'vig_desde' as keyof typeof enrichedItems[number], header: 'Vigencia Desde' },
      { key: 'vig_hasta' as keyof typeof enrichedItems[number], header: 'Vigencia Hasta', render: (item) => <span>{item.vig_hasta ?? '—'}</span> },
      { key: 'estado_vigencia' as keyof typeof enrichedItems[number], header: 'Estado',
        render: (item) => <StatusBadge variant={estadoVariant(item.estado_vigencia)} label={ESTADO_LABEL[item.estado_vigencia] ?? item.estado_vigencia} />,
      },
      { key: 'acciones' as keyof typeof enrichedItems[number], header: 'Acciones',
        render: (item) => (
          <Button size="sm" variant="ghost" onClick={() => openEdit(item)}>
            Editar
          </Button>
        ),
      },
    ],
    []
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/coordinacion/equipos">
          <Button variant="secondary" size="sm">← Volver</Button>
        </Link>
        <h1 className="text-2xl font-bold text-secondary-900">Asignaciones del Tenant</h1>
      </div>

      <Card>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select label="Rol" options={rolOptions} value={filters.rol_id ?? ''}
            onChange={(e) => { setFilters((f) => ({ ...f, rol_id: e.target.value || undefined })); setPage(1); }} />
        </div>
      </Card>

      {isLoading ? <div className="flex justify-center py-12"><Spinner size="lg" /></div> : (
        <>
          <Card>
            <DataTable columns={columns} data={enrichedItems} keyExtractor={(a) => a.id} />
          </Card>
          {response && response.total > 0 && <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />}
        </>
      )}

      <Modal isOpen={!!editItem} onClose={() => setEditItem(null)} title="Editar Asignación">
        <div className="space-y-4">
          <Select label="Materia" placeholder="Sin materia" options={[{ value: '', label: '— Sin materia —' }, ...materiaOptions]}
            value={editMateria} onChange={(e) => setEditMateria(e.target.value)} />
          <Select label="Carrera" placeholder="Sin carrera" options={[{ value: '', label: '— Sin carrera —' }, ...carreraOptions]}
            value={editCarrera} onChange={(e) => setEditCarrera(e.target.value)} />
          <Select label="Cohorte" placeholder="Sin cohorte" options={[{ value: '', label: '— Sin cohorte —' }, ...cohorteOptions]}
            value={editCohorte} onChange={(e) => setEditCohorte(e.target.value)} />
          <Select label="Rol" options={[{ value: '', label: 'Sin cambios' }, ...rolEditOptions]}
            value={editRol} onChange={(e) => setEditRol(e.target.value)} />
          <Input label="Vigencia Desde" type="date" value={editVigDesde} onChange={(e) => setEditVigDesde(e.target.value)} />
          <Input label="Vigencia Hasta" type="date" value={editVigHasta} onChange={(e) => setEditVigHasta(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setEditItem(null)}>Cancelar</Button>
            <Button onClick={handleUpdate} isLoading={updating}>Guardar</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
