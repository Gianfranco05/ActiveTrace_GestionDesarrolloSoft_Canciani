export interface MensajeResponse {
  id: string;
  sender_id: string;
  sender_nombre: string;
  recipient_id: string;
  recipient_nombre: string;
  parent_id: string | null;
  asunto: string;
  cuerpo: string;
  leido: boolean;
  leido_at: string | null;
  created_at: string;
}

export interface InboxThreadResponse {
  thread_id: string;
  asunto: string;
  sender_nombre: string;
  last_message_preview: string;
  message_count: number;
  unread_count: number;
  last_activity: string;
}

export interface ThreadDetailResponse {
  thread: MensajeResponse;
  replies: MensajeResponse[];
}
