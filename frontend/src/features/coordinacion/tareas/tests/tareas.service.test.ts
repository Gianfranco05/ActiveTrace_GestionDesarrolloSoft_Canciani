import { describe, it, expect, vi, beforeEach } from 'vitest';

import api from '@/shared/services/api';

import { getTareas, getTarea, crearTarea, cambiarEstadoTarea, agregarComentario, getComentarios, getHistorial } from '../services/tareas.service';

vi.mock('@/shared/services/api', () => ({ default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() } }));

const mockApi = vi.mocked(api);

describe('TareasService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getTareas fetches paginated list', async () => {
    const mockResponse = { items: [{ id: '1', titulo: 'Tarea 1', estado: 'Pendiente' }], total: 1 };
    mockApi.get.mockResolvedValue({ data: mockResponse });

    const result = await getTareas(1, { estado: 'Pendiente' });

    expect(mockApi.get).toHaveBeenCalledWith('/tareas', { params: { offset: 0, limit: 20, estado: 'Pendiente' } });
    expect(result.data[0].estado).toBe('Pendiente');
  });

  it('getTarea fetches single tarea', async () => {
    mockApi.get.mockResolvedValue({ data: { id: '1', titulo: 'Tarea 1' } });

    const result = await getTarea('1');

    expect(mockApi.get).toHaveBeenCalledWith('/tareas/1');
    expect(result.titulo).toBe('Tarea 1');
  });

  it('crearTarea posts and returns new tarea', async () => {
    const payload = {
      titulo: 'Nueva tarea',
      descripcion: 'Descripción',
      materia_id: 'm1',
      docente_asignado_id: 'd1',
      criterio_cierre: 'Criterio',
    };
    mockApi.post.mockResolvedValue({ data: { id: '1', ...payload, estado: 'Pendiente' } });

    const result = await crearTarea(payload);

    expect(mockApi.post).toHaveBeenCalledWith('/tareas', payload);
    expect(result.estado).toBe('Pendiente');
  });

  it('cambiarEstadoTarea patches estado', async () => {
    mockApi.patch.mockResolvedValue({ data: { id: '1', estado: 'En progreso' } });

    const result = await cambiarEstadoTarea('1', 'En progreso');

    expect(mockApi.patch).toHaveBeenCalledWith('/tareas/1', { estado: 'En progreso' });
    expect(result.estado).toBe('En progreso');
  });

  it('cambiarEstadoTarea cancels from any state', async () => {
    mockApi.patch.mockResolvedValue({ data: { id: '1', estado: 'Cancelada' } });

    const result = await cambiarEstadoTarea('1', 'Cancelada');

    expect(result.estado).toBe('Cancelada');
  });

  it('cambiarEstadoTarea resolves to completada', async () => {
    mockApi.patch.mockResolvedValue({ data: { id: '1', estado: 'Resuelta' } });

    const result = await cambiarEstadoTarea('1', 'Resuelta');

    expect(result.estado).toBe('Resuelta');
  });

  it('agregarComentario posts comment', async () => {
    mockApi.post.mockResolvedValue({ data: { id: 'c1', tarea_id: '1', autor_nombre: 'User', contenido: 'Test', created_at: '2026-01-01' } });

    const result = await agregarComentario('1', 'Test');

    expect(mockApi.post).toHaveBeenCalledWith('/tareas/1/comentarios', { contenido: 'Test' });
    expect(result.contenido).toBe('Test');
  });

  it('getComentarios fetches comments', async () => {
    mockApi.get.mockResolvedValue({ data: [{ id: 'c1', contenido: 'Test' }] });

    const result = await getComentarios('1');

    expect(mockApi.get).toHaveBeenCalledWith('/tareas/1/comentarios');
    expect(result).toHaveLength(1);
  });

  it('getHistorial fetches state change history', async () => {
    const mockHistorial = [
      { id: 'h1', tarea_id: '1', estado_anterior: 'Pendiente', estado_nuevo: 'En progreso', usuario_nombre: 'Admin', created_at: '2026-01-01' },
    ];
    mockApi.get.mockResolvedValue({ data: mockHistorial });

    const result = await getHistorial('1');

    expect(mockApi.get).toHaveBeenCalledWith('/tareas/1/historial');
    expect(result[0].estado_nuevo).toBe('En progreso');
  });
});
