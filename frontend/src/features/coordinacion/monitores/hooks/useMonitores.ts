import { useQuery, useInfiniteQuery } from '@tanstack/react-query';

import {
  getMonitorGeneral,
  getMonitorGeneralInfinito,
  getMonitorDocente,
} from '@/features/coordinacion/monitores/services/monitores.service';

import type {
  MonitorGeneralRow,
  MonitorDocenteRow,
  MonitorGeneralFilters,
  MonitorDocenteFilters,
} from '@/features/coordinacion/monitores/types/monitores.types';

export function useMonitorGeneral(page: number, filters?: MonitorGeneralFilters) {
  return useQuery<{ data: MonitorGeneralRow[]; total: number; page: number; total_pages: number }>({
    queryKey: ['monitor-general', page, filters],
    queryFn: () => getMonitorGeneral(page, filters),
  });
}

export function useMonitorGeneralInfinito(filters?: MonitorGeneralFilters) {
  return useInfiniteQuery({
    queryKey: ['monitor-general-infinito', filters],
    queryFn: ({ pageParam }) => getMonitorGeneralInfinito(pageParam as string | undefined, filters),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  });
}

export function useMonitorDocente(page: number, filters?: MonitorDocenteFilters) {
  return useQuery<{ data: MonitorDocenteRow[]; total: number; page: number; total_pages: number }>({
    queryKey: ['monitor-docente', page, filters],
    queryFn: () => getMonitorDocente(page, filters),
  });
}
