import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { getSalariosBase, createSalarioBase, updateSalarioBase, deleteSalarioBase } from '@/features/finanzas/services/salario.service';

import type { CreateSalarioBasePayload } from '@/features/finanzas/types/salario.types';

export function useSalariosBase() {
  return useQuery({
    queryKey: ['salarios', 'base'],
    queryFn: getSalariosBase,
  });
}

export function useMutateSalarioBase() {
  const queryClient = useQueryClient();

  const create = useMutation({
    mutationFn: (payload: CreateSalarioBasePayload) => createSalarioBase(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios', 'base'] }),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreateSalarioBasePayload> }) =>
      updateSalarioBase(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios', 'base'] }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => deleteSalarioBase(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios', 'base'] }),
  });

  return { create, update, remove };
}
