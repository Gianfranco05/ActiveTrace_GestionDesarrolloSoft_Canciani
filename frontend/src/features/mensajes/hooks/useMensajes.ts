import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  listarInbox,
  verHilo,
  enviarMensaje,
  responderHilo,
} from '@/features/mensajes/services/mensajes.service';

export function useInbox(offset = 0, limit = 20) {
  return useQuery({
    queryKey: ['inbox', offset, limit],
    queryFn: () => listarInbox(offset, limit),
  });
}

export function useHilo(threadId: string | null) {
  return useQuery({
    queryKey: ['inbox', 'thread', threadId],
    queryFn: () => verHilo(threadId!),
    enabled: !!threadId,
  });
}

export function useEnviarMensaje() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: { recipient_id: string; asunto: string; cuerpo: string }) =>
      enviarMensaje(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
    },
  });
}

export function useResponderHilo(threadId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (cuerpo: string) => responderHilo(threadId, cuerpo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
      queryClient.invalidateQueries({ queryKey: ['inbox', 'thread', threadId] });
    },
  });
}
