import { useQuery } from '@tanstack/react-query';

import { getAccionesPorDia, getEstadoComunicaciones, getInteraccionesDocente, getUltimasAcciones, getLogAuditoria } from '@/features/admin/services/auditoria.service';

import type { AuditoriaFilter } from '@/features/admin/types/auditoria.types';

export function useMetricasAuditoria(filter?: AuditoriaFilter) {
  const acciones = useQuery({
    queryKey: ['auditoria', 'acciones-por-dia', filter],
    queryFn: () => getAccionesPorDia(filter),
  });

  const estados = useQuery({
    queryKey: ['auditoria', 'estado-comunicaciones', filter],
    queryFn: () => getEstadoComunicaciones(filter),
  });

  const interacciones = useQuery({
    queryKey: ['auditoria', 'interacciones', filter],
    queryFn: () => getInteraccionesDocente(filter),
  });

  const ultimas = useQuery({
    queryKey: ['auditoria', 'ultimas-acciones'],
    queryFn: () => getUltimasAcciones(200),
  });

  return {
    accionesPorDia: acciones,
    estadoComunicaciones: estados,
    interaccionesDocente: interacciones,
    ultimasAcciones: ultimas,
  };
}

export function useLogAuditoria(filter?: AuditoriaFilter) {
  return useQuery({
    queryKey: ['auditoria', 'log', filter],
    queryFn: () => getLogAuditoria(filter),
  });
}
