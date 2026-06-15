export interface ComunicacionPreview {
  alumnoId: string;
  alumnoNombre: string;
  asunto: string;
  cuerpo: string;
  destinatario: string;
}

export interface EstadoComunicacion {
  id: string;
  destinatario: string;
  estado: 'Pendiente' | 'Enviando' | 'Enviado' | 'Error' | 'Cancelado';
  fechaEnvio?: string;
}

export interface LoteEnvio {
  id: string;
  alumnoId: string;
  alumnoNombre: string;
  estado: 'Pendiente' | 'Enviando' | 'Enviado' | 'Error' | 'Cancelado';
}
