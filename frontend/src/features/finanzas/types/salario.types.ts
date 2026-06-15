export interface SalarioBase {
  id: string;
  rol: string;
  monto: number;
  desde: string;
  hasta: string | null;
  activo: boolean;
}

export interface SalarioPlus {
  id: string;
  grupo: string;
  rol: string;
  descripcion: string;
  monto: number;
  desde: string;
  hasta: string | null;
  activo: boolean;
}

export interface CreateSalarioBasePayload {
  rol: string;
  monto: number;
  desde: string;
  hasta?: string | null;
}

export interface CreateSalarioPlusPayload {
  grupo: string;
  rol: string;
  descripcion: string;
  monto: number;
  desde: string;
  hasta?: string | null;
}
