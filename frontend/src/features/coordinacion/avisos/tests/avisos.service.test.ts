import { describe, it, expect, vi, beforeEach } from 'vitest';

import api from '@/shared/services/api';

import { getAvisos, getAviso, crearAviso, editarAviso, eliminarAviso, getAcuses } from '../services/avisos.service';

vi.mock('@/shared/services/api', () => ({ default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() } }));

const mockApi = vi.mocked(api);

describe('AvisosService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getAvisos fetches paginated list', async () => {
    const mockResponse = { items: [{ id: '1', titulo: 'Test' }], total: 1 };
    mockApi.get.mockResolvedValue({ data: mockResponse });

    const result = await getAvisos(1, { alcance: 'Global' });

    expect(mockApi.get).toHaveBeenCalledWith('/avisos', { params: { offset: 0, limit: 20, admin: true, alcance: 'Global' } });
    expect(result.data).toHaveLength(1);
  });

  it('getAviso fetches single aviso', async () => {
    const mockAviso = { id: '1', titulo: 'Test' };
    mockApi.get.mockResolvedValue({ data: mockAviso });

    const result = await getAviso('1');

    expect(mockApi.get).toHaveBeenCalledWith('/avisos/1');
    expect(result.titulo).toBe('Test');
  });

  it('crearAviso posts form data', async () => {
    const payload = {
      titulo: 'Nuevo aviso',
      cuerpo: 'Contenido',
      alcance: 'Global' as const,
      rol_destino: 'profesor',
      severidad: 'Critico' as const,
      orden: 1,
      inicio_en: new Date().toISOString(),
      fin_en: new Date().toISOString(),
      activo: true,
      requiere_ack: false,
    };
    mockApi.post.mockResolvedValue({ data: { id: '1', ...payload } });

    const result = await crearAviso(payload);

    expect(mockApi.post).toHaveBeenCalledWith('/avisos', payload);
    expect(result.id).toBe('1');
  });

  it('editarAviso updates aviso', async () => {
    const payload = {
      titulo: 'Actualizado',
      cuerpo: 'Nuevo contenido',
      alcance: 'PorCohorte' as const,
      rol_destino: 'alumno',
      severidad: 'Advertencia' as const,
      orden: 2,
      inicio_en: new Date().toISOString(),
      fin_en: new Date().toISOString(),
      activo: false,
      requiere_ack: true,
    };
    mockApi.put.mockResolvedValue({ data: { id: '1', ...payload } });

    const result = await editarAviso('1', payload);

    expect(mockApi.put).toHaveBeenCalledWith('/avisos/1', payload);
    expect(result.activo).toBe(false);
  });

  it('eliminarAviso deletes aviso', async () => {
    mockApi.delete.mockResolvedValue({ data: {} });

    await eliminarAviso('1');

    expect(mockApi.delete).toHaveBeenCalledWith('/avisos/1');
  });

  it('getAcuses fetches acuses for aviso', async () => {
    const mockAcuses = [
      { id: 'a1', aviso_id: '1', usuario_id: 'u1', usuario_nombre: 'User', confirmado: true, confirmado_at: '2026-01-01' },
    ];
    mockApi.get.mockResolvedValue({ data: mockAcuses });

    const result = await getAcuses('1');

    expect(mockApi.get).toHaveBeenCalledWith('/avisos/1/acuses');
    expect(result).toHaveLength(1);
    expect(result[0].confirmado).toBe(true);
  });

  it('getAvisos with requiere_ack aviso returns acuse count', async () => {
    const mockResponse = {
      items: [{ id: '1', titulo: 'Test', requiere_ack: true, total_acuses: 10, acuses_confirmados: 7 }],
      total: 1,
    };
    mockApi.get.mockResolvedValue({ data: mockResponse });

    const result = await getAvisos(1);
    const aviso = result.data[0];

    expect(aviso.requiere_ack).toBe(true);
    expect(aviso.acuses_confirmados).toBe(7);
    expect(aviso.total_acuses).toBe(10);
  });

  it('crearAviso with requiere_ack creates aviso with acknowledgment', async () => {
    const payload = {
      titulo: 'Con confirmación',
      cuerpo: 'Cuerpo',
      alcance: 'Global' as const,
      rol_destino: 'profesor',
      severidad: 'Critico' as const,
      orden: 1,
      activo: true,
      inicio_en: new Date().toISOString(),
      fin_en: new Date().toISOString(),
      requiere_ack: true,
    };
    mockApi.post.mockResolvedValue({ data: { id: '2', ...payload } });

    const result = await crearAviso(payload);

    expect(result.requiere_ack).toBe(true);
  });
});
