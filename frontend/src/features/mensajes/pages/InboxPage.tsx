import { useState } from 'react';
import { toast } from 'sonner';

import { useInbox, useHilo, useResponderHilo } from '@/features/mensajes/hooks/useMensajes';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Spinner } from '@/shared/components/ui/Spinner';

import type { InboxThreadResponse } from '../types/mensajes.types';

function ThreadRow({
  thread,
  onSelect,
  isSelected,
}: {
  thread: InboxThreadResponse;
  onSelect: () => void;
  isSelected: boolean;
}) {
  return (
    <button
      onClick={onSelect}
      className={`w-full border-b border-secondary-100 px-4 py-3 text-left transition-colors last:border-b-0 hover:bg-secondary-50 ${
        isSelected ? 'bg-primary-50' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className={`text-sm ${thread.unread_count > 0 ? 'font-semibold text-secondary-900' : 'text-secondary-600'}`}>
            {thread.asunto}
          </p>
          <p className="mt-1 text-xs text-secondary-400">{thread.sender_nombre}</p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1">
          <span className="text-xs text-secondary-400">
            {new Date(thread.last_activity).toLocaleDateString('es-AR')}
          </span>
          {thread.unread_count > 0 && (
            <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-primary-600 px-1.5 text-xs font-medium text-white">
              {thread.unread_count}
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

function ThreadDetail({
  threadId,
  onBack,
}: {
  threadId: string;
  onBack: () => void;
}) {
  const { data, isLoading } = useHilo(threadId);
  const responder = useResponderHilo(threadId);
  const [replyText, setReplyText] = useState('');

  const handleReply = (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim()) return;

    responder.mutate(replyText.trim(), {
      onSuccess: () => {
        toast.success('Respuesta enviada');
        setReplyText('');
      },
      onError: () => toast.error('No se pudo enviar la respuesta'),
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-4 text-center text-sm text-secondary-500">
        No se pudo cargar la conversación.
      </div>
    );
  }

  const allMensajes = [data.thread, ...data.replies];

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b border-secondary-200 px-4 py-3">
        <Button variant="ghost" size="sm" onClick={onBack}>
          &larr; Volver
        </Button>
        <h2 className="text-sm font-semibold text-secondary-900 truncate">
          {data.thread.asunto}
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 p-4">
        {allMensajes.map((msg) => (
          <Card key={msg.id} className={`max-w-[80%] ${msg.id === data.thread.id ? '' : 'ml-auto bg-primary-50 border-primary-100'}`}>
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-medium text-secondary-700">{msg.sender_nombre}</p>
              <p className="text-xs text-secondary-400">
                {new Date(msg.created_at).toLocaleString('es-AR')}
              </p>
            </div>
            <p className="mt-2 whitespace-pre-wrap text-sm text-secondary-600">
              {msg.cuerpo}
            </p>
          </Card>
        ))}
      </div>

      <form onSubmit={handleReply} className="border-t border-secondary-200 p-4">
        <div className="flex gap-2">
          <input
            className="block w-full rounded-lg border border-secondary-300 px-3 py-2 text-sm shadow-sm placeholder:text-secondary-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1"
            placeholder="Escribí tu respuesta..."
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
          />
          <Button
            type="submit"
            size="sm"
            isLoading={responder.isPending}
            disabled={!replyText.trim()}
          >
            Enviar
          </Button>
        </div>
      </form>
    </div>
  );
}

export function InboxPage() {
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const { data: threads, isLoading } = useInbox();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Inbox</h1>
        <p className="mt-1 text-sm text-secondary-500">
          Mensajería interna — consultá y respondé mensajes.
        </p>
      </div>

      <Card className="overflow-hidden">
        <div className="flex h-[calc(100vh-16rem)]">
          <div className={`w-full border-r border-secondary-200 overflow-y-auto ${selectedThreadId ? 'hidden md:block md:w-80 lg:w-96' : ''}`}>
            {isLoading ? (
              <div className="flex justify-center py-8">
                <Spinner size="lg" />
              </div>
            ) : threads && threads.length > 0 ? (
              threads.map((thread) => (
                <ThreadRow
                  key={thread.thread_id}
                  thread={thread}
                  isSelected={selectedThreadId === thread.thread_id}
                  onSelect={() => setSelectedThreadId(thread.thread_id)}
                />
              ))
            ) : (
              <div className="px-4 py-8 text-center text-sm text-secondary-500">
                No tenés mensajes en el inbox.
              </div>
            )}
          </div>

          {selectedThreadId ? (
            <div className="flex-1 flex-col overflow-hidden hidden md:flex">
              <ThreadDetail
                threadId={selectedThreadId}
                onBack={() => setSelectedThreadId(null)}
              />
            </div>
          ) : (
            <div className="hidden flex-1 items-center justify-center md:flex">
              <p className="text-sm text-secondary-400">
                Seleccioná una conversación para ver su detalle.
              </p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
