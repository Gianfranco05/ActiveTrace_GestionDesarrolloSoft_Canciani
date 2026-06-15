import { describe, it, expect, vi, beforeEach } from 'vitest';

import api from '@/shared/services/api';

import {
  getMisEquipos,
  getAsignaciones,
  asignacionMasiva,
  clonarEquipo,
  modificarVigencia,
} from '../services/equipos.service';

vi.mock('@/shared/services/api', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}));

const mockApi = vi.mocked(api);

describe('EquiposService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getMisEquipos calls correct endpoint', async () => {
    const mockData = { items: [], total: 0, offset: 0, limit: 20 };
    mockApi.get.mockResolvedValue({ data: mockData });

    const result = await getMisEquipos({ estado: 'Vigente' });

    expect(mockApi.get).toHaveBeenCalledWith('/equipos/mis-equipos', {
      params: { estado: 'Vigente' },
    });
    expect(result).toEqual(mockData);
  });

  it('getAsignaciones calls with pagination params', async () => {
    const mockResponse = { items: [], total: 0, offset: 0, limit: 20 };
    mockApi.get.mockResolvedValue({ data: mockResponse });

    const result = await getAsignaciones(1, { rol_id: 'r1' });

    expect(mockApi.get).toHaveBeenCalledWith('/v1/asignaciones', {
      params: { offset: 0, limit: 20, rol_id: 'r1' },
    });
    expect(result).toEqual(mockResponse);
  });

  it('asignacionMasiva posts correct payload', async () => {
    const payload = {
      materia_id: 'm1',
      carrera_id: 'c1',
      cohorte_id: 'ch1',
      rol_id: 'r1',
      usuario_ids: ['u1', 'u2'],
      vig_desde: '2026-01-01',
      vig_hasta: '2026-12-31',
      comisiones: null,
    };
    mockApi.post.mockResolvedValue({ data: { items: [], total: 0, offset: 0, limit: 0 } });

    await asignacionMasiva(payload);

    expect(mockApi.post).toHaveBeenCalledWith('/equipos/masiva', payload);
  });

  it('clonarEquipo posts clone payload', async () => {
    const payload = {
      origen_materia_id: 'm1',
      origen_carrera_id: 'c1',
      origen_cohorte_id: 'co1',
      destino_materia_id: 'm2',
      destino_carrera_id: 'c2',
      destino_cohorte_id: 'cd1',
      nueva_vig_desde: '2026-03-01',
      nueva_vig_hasta: '2026-12-31',
    };
    mockApi.post.mockResolvedValue({
      data: {
        materia_id: 'm2',
        carrera_id: 'c2',
        cohorte_id: 'cd1',
        asignaciones: [],
      },
    });

    const result = await clonarEquipo(payload);

    expect(mockApi.post).toHaveBeenCalledWith('/equipos/clonar', payload);
    expect(result.asignaciones).toEqual([]);
  });

  it('modificarVigencia patches vigencia with query params', async () => {
    mockApi.patch.mockResolvedValue({ data: {} });

    await modificarVigencia({
      materia_id: 'm1',
      carrera_id: 'c1',
      cohorte_id: 'ch1',
      vig_desde: '2026-03-01',
      vig_hasta: '2026-07-01',
    });

    expect(mockApi.patch).toHaveBeenCalledWith(
      '/equipos/vigencia',
      { vig_desde: '2026-03-01', vig_hasta: '2026-07-01' },
      {
        params: {
          materia_id: 'm1',
          carrera_id: 'c1',
          cohorte_id: 'ch1',
        },
      }
    );
  });

  it('clonarEquipo with no assignments returns empty list', async () => {
    const payload = {
      origen_materia_id: 'm1',
      origen_carrera_id: 'c1',
      origen_cohorte_id: 'co1',
      destino_materia_id: 'm2',
      destino_carrera_id: 'c2',
      destino_cohorte_id: 'cd1',
      nueva_vig_desde: '2026-03-01',
      nueva_vig_hasta: null,
    };
    mockApi.post.mockResolvedValue({
      data: {
        materia_id: 'm2',
        carrera_id: 'c2',
        cohorte_id: 'cd1',
        asignaciones: [],
      },
    });

    const result = await clonarEquipo(payload);

    expect(result.asignaciones.length).toBe(0);
  });
});
