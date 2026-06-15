import api from '@/shared/services/api';

import type { Carrera, Cohorte, Materia, CreateCarreraPayload, CreateCohortePayload, CreateMateriaPayload } from '@/features/admin/types/estructura.types';

// Backend returns { estado: "Activa" | "Inactiva" }, frontend expects { activa: boolean }
type RawItem = { id: string; codigo?: string; nombre: string; estado: string; [key: string]: unknown };

function mapEstado<T extends RawItem>(item: T): T & { activa: boolean } {
  return { ...item, activa: item.estado === 'Activa' };
}

function mapItems<T extends RawItem>(items: T[]): (T & { activa: boolean })[] {
  return items.map(mapEstado);
}

// --- Carreras ---

export async function getCarreras(): Promise<Carrera[]> {
  const { data } = await api.get<{ items: RawItem[] }>('/v1/estructura/carreras');
  return mapItems(data.items ?? []) as Carrera[];
}

export async function createCarrera(payload: CreateCarreraPayload): Promise<Carrera> {
  const { data } = await api.post<RawItem>('/v1/estructura/carreras', payload);
  return mapEstado(data) as Carrera;
}

export async function updateCarrera(id: string, payload: Partial<CreateCarreraPayload>): Promise<Carrera> {
  const { data } = await api.put<RawItem>(`/v1/estructura/carreras/${id}`, payload);
  return mapEstado(data) as Carrera;
}

export async function toggleCarreraEstado(id: string): Promise<Carrera> {
  const { data } = await api.patch<RawItem>(`/v1/estructura/carreras/${id}/estado`);
  return mapEstado(data) as Carrera;
}

// --- Cohortes ---

export async function getCohortes(carrera_id?: string): Promise<Cohorte[]> {
  const { data } = await api.get<{ items: RawItem[] }>('/v1/estructura/cohortes', { params: { carrera_id } });
  return mapItems(data.items ?? []) as unknown as Cohorte[];
}

export async function createCohorte(payload: CreateCohortePayload): Promise<Cohorte> {
  const { data } = await api.post<RawItem>('/v1/estructura/cohortes', payload);
  return mapEstado(data) as unknown as Cohorte;
}

export async function updateCohorte(id: string, payload: Partial<CreateCohortePayload>): Promise<Cohorte> {
  const { data } = await api.put<RawItem>(`/v1/estructura/cohortes/${id}`, payload);
  return mapEstado(data) as unknown as Cohorte;
}

export async function toggleCohorteEstado(id: string): Promise<Cohorte> {
  const { data } = await api.patch<RawItem>(`/v1/estructura/cohortes/${id}/estado`);
  return mapEstado(data) as unknown as Cohorte;
}

// --- Materias ---

export async function getMaterias(): Promise<Materia[]> {
  const { data } = await api.get<{ items: RawItem[] }>('/v1/estructura/materias');
  return mapItems(data.items ?? []) as Materia[];
}

export async function createMateria(payload: CreateMateriaPayload): Promise<Materia> {
  const { data } = await api.post<RawItem>('/v1/estructura/materias', payload);
  return mapEstado(data) as Materia;
}

export async function updateMateria(id: string, payload: Partial<CreateMateriaPayload>): Promise<Materia> {
  const { data } = await api.put<RawItem>(`/v1/estructura/materias/${id}`, payload);
  return mapEstado(data) as Materia;
}

export async function toggleMateriaEstado(id: string): Promise<Materia> {
  const { data } = await api.patch<RawItem>(`/v1/estructura/materias/${id}/estado`);
  return mapEstado(data) as Materia;
}
