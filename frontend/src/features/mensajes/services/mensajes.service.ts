import api from '@/shared/services/api';

import type { InboxThreadResponse, ThreadDetailResponse, MensajeResponse } from '../types/mensajes.types';

export async function listarInbox(offset = 0, limit = 20): Promise<InboxThreadResponse[]> {
  const { data } = await api.get('/inbox', { params: { offset, limit } });
  return data.items;
}

export async function verHilo(threadId: string): Promise<ThreadDetailResponse> {
  const { data } = await api.get(`/inbox/${threadId}`);
  return data;
}

export async function enviarMensaje(body: {
  recipient_id: string;
  asunto: string;
  cuerpo: string;
}): Promise<MensajeResponse> {
  const { data } = await api.post('/inbox', body);
  return data;
}

export async function responderHilo(
  threadId: string,
  cuerpo: string
): Promise<MensajeResponse> {
  const { data } = await api.post(`/inbox/${threadId}/reply`, { cuerpo });
  return data;
}
