import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { getSalariosPlus, createSalarioPlus, updateSalarioPlus, deleteSalarioPlus } from '@/features/finanzas/services/salario.service';

import type { CreateSalarioPlusPayload } from '@/features/finanzas/types/salario.types';

export function useSalariosPlus() {
  return useQuery({
    queryKey: ['salarios', 'plus'],
    queryFn: getSalariosPlus,
  });
}

export function useMutateSalarioPlus() {
  const queryClient = useQueryClient();

  const create = useMutation({
    mutationFn: (payload: CreateSalarioPlusPayload) => createSalarioPlus(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios', 'plus'] }),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreateSalarioPlusPayload> }) =>
      updateSalarioPlus(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios', 'plus'] }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => deleteSalarioPlus(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['salarios', 'plus'] }),
  });

  return { create, update, remove };
}
