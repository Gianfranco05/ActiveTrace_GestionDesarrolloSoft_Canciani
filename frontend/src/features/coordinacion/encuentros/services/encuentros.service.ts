import api from '@/shared/services/api';

import type {
  Encuentro,
  EncuentroRecurrenteForm,
  EncuentroUnicoForm,
  EncuentroEditForm,
  EncuentrosFilters,
  ContenidoAulaVirtual,
} from '@/features/coordinacion/encuentros/types/encuentros.types';

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  total_pages: number;
}

export async function getEncuentros(
  page: number,
  filters?: EncuentrosFilters
): Promise<PaginatedResponse<Encuentro>> {
  const { data } = await api.get('/encuentros', {
    params: { page, ...filters },
  });
  return data;
}

export async function crearEncuentroRecurrente(payload: EncuentroRecurrenteForm): Promise<Encuentro[]> {
  const { data } = await api.post('/encuentros/slots', payload);
  return data;
}

export async function crearEncuentroUnico(payload: EncuentroUnicoForm): Promise<Encuentro> {
  const { data } = await api.post('/encuentros/instancias', payload);
  return data;
}

export async function editarEncuentro(id: string, payload: EncuentroEditForm): Promise<Encuentro> {
  const { data } = await api.patch(`/encuentros/${id}`, payload);
  return data;
}

export async function getContenidoAula(materiaId: string): Promise<ContenidoAulaVirtual> {
  const { data } = await api.get(`/encuentros/${materiaId}/contenido-aula`);
  return data;
}
