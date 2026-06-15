import api from '@/shared/services/api';

import type { Factura, FacturaFilter } from '@/features/finanzas/types/factura.types';

export async function getFacturas(filter?: FacturaFilter): Promise<Factura[]> {
  const { data } = await api.get<Factura[]>('/facturas/', { params: filter });
  return data;
}

export async function createFactura(formData: FormData): Promise<Factura> {
  const { data } = await api.post<Factura>('/facturas/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function cambiarEstadoFactura(id: string, estado: 'Pendiente' | 'Abonada'): Promise<Factura> {
  const { data } = await api.patch<Factura>(`/facturas/${id}/estado`, { estado });
  return data;
}
