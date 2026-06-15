import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import {
  useEncuentros,
  useCrearEncuentroRecurrente,
  useCrearEncuentroUnico,
  useEditarEncuentro,
  useContenidoAula,
} from '@/features/coordinacion/encuentros/hooks/useEncuentros';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { Input } from '@/shared/components/ui/Input';
import { Modal } from '@/shared/components/ui/Modal';
import { Pagination } from '@/shared/components/ui/Pagination';
import { Select } from '@/shared/components/ui/Select';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';
import { useFormModal } from '@/shared/hooks/useFormModal';
import api from '@/shared/services/api';

import type { EncuentrosFilters, EncuentroEditForm } from '@/features/coordinacion/encuentros/types/encuentros.types';
import type { Encuentro } from '@/features/coordinacion/encuentros/types/encuentros.types';

export function EncuentrosPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<EncuentrosFilters>({});
  const [showRecurrente, setShowRecurrente] = useState(false);
  const [showUnico, setShowUnico] = useState(false);
  const [contenidoMateria, setContenidoMateria] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const [recurForm, setRecurForm] = useState({
    materia_id: '', dia_semana: 1, horario: '', fecha_inicio: '', semanas: 12, titulo: '', enlace: '',
  });
  const [unicoForm, setUnicoForm] = useState({
    materia_id: '', fecha: '', horario: '', titulo: '', enlace: '',
  });

  const { data, isLoading } = useEncuentros(page, filters);
  const { mutateAsync: crearRec, isPending: creatingRec } = useCrearEncuentroRecurrente();
  const { mutateAsync: crearUnico, isPending: creatingUnico } = useCrearEncuentroUnico();
  const { mutateAsync: editar } = useEditarEncuentro();
  const { data: contenido } = useContenidoAula(contenidoMateria ?? '');

  const { data: materias = [] } = useQuery<{ id: string; nombre: string; codigo: string }[]>({
    queryKey: ['materias-encuentro'],
    queryFn: async () => {
      const { data } = await api.get<{ items: { id: string; nombre: string; codigo: string }[] }>('/v1/estructura/materias');
      return data.items ?? [];
    },
  });

  const materiaOptions = [{ value: '', label: '— Todas —' }, ...materias.map((m) => ({ value: m.id, label: `${m.codigo} — ${m.nombre}` }))];

  const {
    isOpen: editOpen,
    selectedItem: editItem,
    formData: editFormData,
    openEdit,
    close: closeEdit,
    setFormData: setEditFormData,
  } = useFormModal<EncuentroEditForm, Encuentro>({ estado: undefined, enlace: '', grabacion: '', comentario: '' });

  const columns = useMemo<Column[]>(
    () => [
      { key: 'fecha', header: 'Fecha' },
      { key: 'horario', header: 'Horario' },
      { key: 'materia_nombre', header: 'Materia' },
      { key: 'docente_nombre', header: 'Docente' },
      {
        key: 'enlace',
        header: 'Enlace',
        render: (item) => item.enlace ? <a href={item.enlace} className="text-primary-600 hover:text-primary-500 text-sm" target="_blank">Ver</a> : '—',
      },
      {
        key: 'estado',
        header: 'Estado',
        render: (item) => {
          const variant = item.estado === 'realizado' ? 'success' : item.estado === 'cancelado' ? 'error' : item.estado === 'pendiente' ? 'pending' : 'info';
          return <StatusBadge variant={variant} label={item.estado} />;
        },
      },
      {
        key: 'acciones',
        header: 'Acciones',
        render: (item) => (
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="ghost"
              aria-label="Editar encuentro"
              onClick={(e) => {
                e.stopPropagation();
                openEdit(item, { estado: item.estado, enlace: item.enlace ?? '', grabacion: item.grabacion ?? '', comentario: item.comentario ?? '' });
              }}
            >
              Editar
            </Button>
          </div>
        ),
      },
    ],
    [openEdit]
  );

  const handleCopy = async () => {
    if (contenido?.contenido) {
      await navigator.clipboard.writeText(contenido.contenido);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-secondary-900">Encuentros</h1>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => setShowRecurrente(!showRecurrente)}>
            {showRecurrente ? 'Ocultar' : 'Nuevo Recurrente'}
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setShowUnico(!showUnico)}>
            {showUnico ? 'Ocultar' : 'Nuevo Único'}
          </Button>
        </div>
      </div>

      {showRecurrente && (
        <Card header={<h3 className="font-semibold">Encuentro Recurrente</h3>}>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Materia" placeholder="Seleccionar materia" options={materiaOptions} value={recurForm.materia_id} onChange={(e) => setRecurForm((f) => ({ ...f, materia_id: e.target.value }))} />
            <Select
              label="Día de semana"
              options={[
                { value: '0', label: 'Domingo' }, { value: '1', label: 'Lunes' }, { value: '2', label: 'Martes' },
                { value: '3', label: 'Miércoles' }, { value: '4', label: 'Jueves' }, { value: '5', label: 'Viernes' }, { value: '6', label: 'Sábado' },
              ]}
              value={String(recurForm.dia_semana)}
              onChange={(e) => setRecurForm((f) => ({ ...f, dia_semana: Number(e.target.value) }))}
            />
            <Input label="Horario" type="time" value={recurForm.horario} onChange={(e) => setRecurForm((f) => ({ ...f, horario: e.target.value }))} />
            <Input label="Fecha Inicio" type="date" value={recurForm.fecha_inicio} onChange={(e) => setRecurForm((f) => ({ ...f, fecha_inicio: e.target.value }))} />
            <Input label="Semanas" type="number" min={1} value={recurForm.semanas} onChange={(e) => setRecurForm((f) => ({ ...f, semanas: Number(e.target.value) }))} />
            <Input label="Título" value={recurForm.titulo} onChange={(e) => setRecurForm((f) => ({ ...f, titulo: e.target.value }))} />
            <Input label="Enlace" value={recurForm.enlace} onChange={(e) => setRecurForm((f) => ({ ...f, enlace: e.target.value }))} />
          </div>
          <div className="mt-4 flex justify-end">
            <Button onClick={async () => { await crearRec(recurForm); setShowRecurrente(false); }} isLoading={creatingRec}>Crear Serie</Button>
          </div>
        </Card>
      )}

      {showUnico && (
        <Card header={<h3 className="font-semibold">Encuentro Único</h3>}>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Materia" placeholder="Seleccionar materia" options={materiaOptions} value={unicoForm.materia_id} onChange={(e) => setUnicoForm((f) => ({ ...f, materia_id: e.target.value }))} />
            <Input label="Fecha" type="date" value={unicoForm.fecha} onChange={(e) => setUnicoForm((f) => ({ ...f, fecha: e.target.value }))} />
            <Input label="Horario" type="time" value={unicoForm.horario} onChange={(e) => setUnicoForm((f) => ({ ...f, horario: e.target.value }))} />
            <Input label="Título" value={unicoForm.titulo} onChange={(e) => setUnicoForm((f) => ({ ...f, titulo: e.target.value }))} />
            <Input label="Enlace" value={unicoForm.enlace} onChange={(e) => setUnicoForm((f) => ({ ...f, enlace: e.target.value }))} />
          </div>
          <div className="mt-4 flex justify-end">
            <Button onClick={async () => { await crearUnico(unicoForm); setShowUnico(false); }} isLoading={creatingUnico}>Crear Encuentro</Button>
          </div>
        </Card>
      )}

      <Card>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Select label="Materia" placeholder="Todas" options={materiaOptions} value={filters.materia_id ?? ''} onChange={(e) => setFilters((f) => ({ ...f, materia_id: e.target.value || undefined }))} />
          <Input label="Buscar" placeholder="Docente o título..." value={filters.q ?? ''} onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value || undefined }))} />
          <div className="grid grid-cols-2 gap-2">
            <Input label="Desde" type="date" value={filters.fecha_desde ?? ''} onChange={(e) => setFilters((f) => ({ ...f, fecha_desde: e.target.value || undefined }))} />
            <Input label="Hasta" type="date" value={filters.fecha_hasta ?? ''} onChange={(e) => setFilters((f) => ({ ...f, fecha_hasta: e.target.value || undefined }))} />
          </div>
        </div>
      </Card>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : (
        <>
          <Card>
            <DataTable columns={columns} data={data?.data ?? []} keyExtractor={(e) => e.id} />
          </Card>
          {data && <Pagination page={data.page} totalPages={data.total_pages} onPageChange={setPage} />}
        </>
      )}

      <Modal isOpen={editOpen} onClose={closeEdit} title="Editar Instancia">
        <div className="space-y-4">
          <Select
            label="Estado"
            options={[
              { value: 'programado', label: 'Programado' },
              { value: 'realizado', label: 'Realizado' },
              { value: 'cancelado', label: 'Cancelado' },
              { value: 'pendiente', label: 'Pendiente' },
            ]}
            value={editFormData.estado ?? ''}
            onChange={(e) => setEditFormData((f) => ({ ...f, estado: e.target.value as EncuentroEditForm['estado'] }))}
          />
          <Input label="Enlace" value={editFormData.enlace ?? ''} onChange={(e) => setEditFormData((f) => ({ ...f, enlace: e.target.value }))} />
          <Input label="Grabación" value={editFormData.grabacion ?? ''} onChange={(e) => setEditFormData((f) => ({ ...f, grabacion: e.target.value }))} />
          <Input label="Comentario" value={editFormData.comentario ?? ''} onChange={(e) => setEditFormData((f) => ({ ...f, comentario: e.target.value }))} />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={closeEdit}>Cancelar</Button>
            <Button onClick={async () => { if (editItem) { await editar({ id: editItem.id, payload: editFormData }); closeEdit(); } }}>Guardar</Button>
          </div>
        </div>
      </Modal>

      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Select label="Materia" placeholder="Seleccionar" options={materiaOptions} value={contenidoMateria ?? ''} onChange={(e) => setContenidoMateria(e.target.value || null)} />
            <Button className="mt-5" size="sm" onClick={() => setContenidoMateria(contenidoMateria)}>Generar contenido</Button>
          </div>
        </div>
        {contenido && (
          <div className="mt-4">
            <pre className="rounded-lg bg-secondary-50 p-4 text-sm whitespace-pre-wrap">{contenido.contenido}</pre>
            <div className="mt-2 flex justify-end">
              <Button size="sm" onClick={handleCopy}>
                {copySuccess ? '✓ Copiado' : 'Copiar al portapapeles'}
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
