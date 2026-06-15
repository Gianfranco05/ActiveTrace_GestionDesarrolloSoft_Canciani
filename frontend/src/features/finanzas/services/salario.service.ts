import api from '@/shared/services/api';

import type { SalarioBase, SalarioPlus, CreateSalarioBasePayload, CreateSalarioPlusPayload } from '@/features/finanzas/types/salario.types';

export async function getSalariosBase(): Promise<SalarioBase[]> {
  const { data } = await api.get<SalarioBase[]>('/salarios/base');
  return data;
}

export async function createSalarioBase(payload: CreateSalarioBasePayload): Promise<SalarioBase> {
  const { data } = await api.post<SalarioBase>('/salarios/base', payload);
  return data;
}

export async function updateSalarioBase(id: string, payload: Partial<CreateSalarioBasePayload>): Promise<SalarioBase> {
  const { data } = await api.put<SalarioBase>(`/salarios/base/${id}`, payload);
  return data;
}

export async function deleteSalarioBase(id: string): Promise<void> {
  await api.delete(`/salarios/base/${id}`);
}

export async function getSalariosPlus(): Promise<SalarioPlus[]> {
  const { data } = await api.get<SalarioPlus[]>('/salarios/plus');
  return data;
}

export async function createSalarioPlus(payload: CreateSalarioPlusPayload): Promise<SalarioPlus> {
  const { data } = await api.post<SalarioPlus>('/salarios/plus', payload);
  return data;
}

export async function updateSalarioPlus(id: string, payload: Partial<CreateSalarioPlusPayload>): Promise<SalarioPlus> {
  const { data } = await api.put<SalarioPlus>(`/salarios/plus/${id}`, payload);
  return data;
}

export async function deleteSalarioPlus(id: string): Promise<void> {
  await api.delete(`/salarios/plus/${id}`);
}
