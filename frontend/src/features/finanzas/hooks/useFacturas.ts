import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { getFacturas, createFactura, cambiarEstadoFactura } from '@/features/finanzas/services/factura.service';

import type { FacturaFilter } from '@/features/finanzas/types/factura.types';

export function useFacturas(filter?: FacturaFilter) {
  return useQuery({
    queryKey: ['facturas', filter],
    queryFn: () => getFacturas(filter),
  });
}

export function useMutateFactura() {
  const queryClient = useQueryClient();

  const create = useMutation({
    mutationFn: (formData: FormData) => createFactura(formData),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facturas'] }),
  });

  const changeEstado = useMutation({
    mutationFn: ({ id, estado }: { id: string; estado: 'Pendiente' | 'Abonada' }) =>
      cambiarEstadoFactura(id, estado),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facturas'] }),
  });

  return { create, changeEstado };
}
