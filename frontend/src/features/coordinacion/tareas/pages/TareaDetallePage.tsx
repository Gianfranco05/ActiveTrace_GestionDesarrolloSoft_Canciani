import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';

import {
  useTarea,
  useCambiarEstadoTarea,
  useComentarios,
  useAgregarComentario,
  useHistorial,
} from '@/features/coordinacion/tareas/hooks/useTareas';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';
import { Textarea } from '@/shared/components/ui/Textarea';

import type { TareaEstado } from '@/features/coordinacion/tareas/types/tareas.types';

const estadoBadge: Record<TareaEstado, 'pending' | 'progress' | 'resolved' | 'cancelled'> = {
  'Pendiente': 'pending',
  'En progreso': 'progress',
  'Resuelta': 'resolved',
  'Cancelada': 'cancelled',
};

export function TareaDetallePage() {
  const { id } = useParams<{ id: string }>();
  const { data: tarea, isLoading } = useTarea(id!);
  const { mutateAsync: cambiarEstado } = useCambiarEstadoTarea();
  const { data: comentarios, isLoading: loadingComentarios } = useComentarios(id!);
  const { data: historial } = useHistorial(id!);
  const { mutateAsync: agregarComentario, isPending: addingComment } = useAgregarComentario();
  const [nuevoComentario, setNuevoComentario] = useState('');

  if (isLoading) {
    return <div className="flex justify-center py-12"><Spinner size="lg" /></div>;
  }

  if (!tarea) {
    return <div className="py-12 text-center text-secondary-500">Tarea no encontrada</div>;
  }

  const handleComentar = async () => {
    if (!nuevoComentario.trim()) return;
    await agregarComentario({ tareaId: id!, contenido: nuevoComentario });
    setNuevoComentario('');
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Link to="/coordinacion/tareas" className="text-sm text-primary-600 hover:text-primary-500">
        &larr; Volver a Tareas
      </Link>

      <Card>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-secondary-900">{tarea.titulo}</h1>
            <StatusBadge variant={estadoBadge[tarea.estado]} label={tarea.estado} />
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><strong>Docente:</strong> {tarea.docente_asignado_nombre}</div>
            <div><strong>Materia:</strong> {tarea.materia_nombre}</div>
            <div><strong>Asignador:</strong> {tarea.asignador_nombre}</div>
            <div><strong>Creado:</strong> {tarea.created_at}</div>
          </div>

          {tarea.descripcion && <p className="text-sm text-secondary-600">{tarea.descripcion}</p>}
          {tarea.criterio_cierre && (
            <div>
              <strong className="text-sm">Criterio de cierre:</strong>
              <p className="text-sm text-secondary-600">{tarea.criterio_cierre}</p>
            </div>
          )}

          {tarea.estado !== 'Cancelada' && tarea.estado !== 'Resuelta' && (
            <div className="flex gap-2">
              {tarea.estado === 'Pendiente' && (
                <Button size="sm" onClick={() => cambiarEstado({ id: id!, estado: 'En progreso' })}>
                  Iniciar
                </Button>
              )}
              {tarea.estado === 'En progreso' && (
                <Button size="sm" onClick={() => cambiarEstado({ id: id!, estado: 'Resuelta' })}>
                  Resolver
                </Button>
              )}
              <Button size="sm" variant="danger" onClick={() => cambiarEstado({ id: id!, estado: 'Cancelada' })}>
                Cancelar
              </Button>
            </div>
          )}
        </div>
      </Card>

      {historial && historial.length > 0 && (
        <Card header={<h3 className="font-semibold text-secondary-900">Historial de Cambios</h3>}>
          <div className="space-y-2">
            {historial.map((h) => (
              <div key={h.id} className="flex items-center gap-2 text-sm">
                <StatusBadge variant={estadoBadge[h.estado_anterior]} label={h.estado_anterior} />
                <span className="text-secondary-400">&rarr;</span>
                <StatusBadge variant={estadoBadge[h.estado_nuevo]} label={h.estado_nuevo} />
                <span className="text-secondary-400">— {h.usuario_nombre}, {h.created_at}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card header={<h3 className="font-semibold text-secondary-900">Comentarios</h3>}>
        <div className="space-y-4">
          {loadingComentarios ? (
            <Spinner />
          ) : comentarios && comentarios.length > 0 ? (
            comentarios.map((c) => (
              <div key={c.id} className="rounded-lg bg-secondary-50 p-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-secondary-700">{c.autor_nombre}</span>
                  <span className="text-xs text-secondary-400">{c.created_at}</span>
                </div>
                <p className="mt-1 text-sm text-secondary-600">{c.contenido}</p>
              </div>
            ))
          ) : (
            <p className="text-sm text-secondary-500">Sin comentarios</p>
          )}

          <div className="space-y-2">
            <Textarea
              label="Nuevo comentario"
              value={nuevoComentario}
              onChange={(e) => setNuevoComentario(e.target.value)}
              placeholder="Escribí un comentario..."
            />
            <div className="flex justify-end">
              <Button size="sm" onClick={handleComentar} isLoading={addingComment} disabled={!nuevoComentario.trim()}>
                Comentar
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
