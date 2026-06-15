## Context

El frontend actual (C-21) provee shell, login, guards de permisos y un cliente HTTP con refresh token. Los cambios C-08 (equipos), C-13 (encuentros), C-14 (coloquios), C-15 (avisos), C-16 (tareas) y C-17 (programas/fechas) exponen endpoints REST que necesitan una interfaz de usuario. Este change construye todas las pantallas del rol COORDINADOR/ADMIN como un feature module unificado `features/coordinacion/`.

## Goals / Non-Goals

**Goals:**
- Feature module `features/coordinacion/` con sub-módulos independientes para equipos, avisos, tareas, encuentros, coloquios, monitores y setup
- Cada sub-módulo sigue el patrón `{components,hooks,services,types,pages}` establecido en C-21
- Guards de permiso fino (`equipos:asignar`, `avisos:publicar`, `tareas:gestionar`, etc.)
- Formularios con React Hook Form + Zod, server state con TanStack Query v5
- Dashboard de coordinación como landing page con KPIs y acceso rápido a cada módulo
- Operaciones masivas (asignación, clonar) con formularios multi-step wizard
- Workflow visual de tareas con indicadores de estado y transiciones

**Non-Goals:**
- No modificar el backend — solo consumir APIs existentes
- No implementar funcionalidades de ALUMNO o TUTOR (eso es C-22)
- No implementar panel de auditoría, liquidaciones ni estructura académica (eso es C-24)
- No modificar Sidebar existente (solo agregar ítems de menú)
- No implementar SSR, SEO ni PWA

## Decisions

### D1: Feature module unificado con sub-módulos

**Decisión**: `features/coordinacion/` como módulo raíz con sub-directorios `equipos/`, `avisos/`, `tareas/`, `encuentros/`, `coloquios/`, `monitores/`, `setup/`.

**Alternativa considerada**: Feature modules separados (`features/equipos/`, `features/avisos/`, etc.).
**Rechazada porque**: agrupar bajo `coordinacion/` refleja el agrupamiento del rol y evita que el directorio `features/` se sature con 7 módulos nuevos. Además, comparten contexto de permisos y patrones de UI.

**Racional**: El agrupamiento por rol es más mantenible que por funcionalidad aislada. Si en el futuro se reutilizan componentes entre roles, se extraen a `shared/`.

### D2: Sub-módulos con pages planas (no nested routes)

**Decisión**: Cada sub-módulo expone páginas planas (ej. `/coordinacion/equipos`, `/coordinacion/equipos/asignacion-masiva`). No se usa layout anidado dentro de coordinacion.

**Alternativa considerada**: Layout anidado con tabs o sidebar interno para coordinacion.
**Rechazada porque**: el AppLayout global ya provee Sidebar y Topbar; un segundo nivel de navegación agrega complejidad innecesaria. Cada página es autosuficiente con su propio header y breadcrumbs.

### D3: Servicios API con TanStack Query hooks

**Decisión**: Cada sub-módulo tiene su `services/` con funciones que llaman a `api` (Axios) y `hooks/` con custom hooks de TanStack Query (`useQuery`, `useMutation`).

**Racional**: Patrón consistente con el feature `auth/` existente. TanStack Query maneja caching, invalidación y estados de loading/error. Los hooks son la interfaz pública del módulo.

### D4: Formularios multi-step con React Hook Form + estado local

**Decisión**: Para operaciones masivas (asignación masiva, clonar equipos) se usa un wizard con estado local (`useState` para step actual) y React Hook Form con validación Zod por paso. No se usa TanStack Query para el estado del wizard.

**Racional**: El estado del wizard es efímero y no necesita cache. React Hook Form maneja la validación por campo y Zod provee schemas tipados reutilizables.

### D5: Workflow de tareas con estados visuales + mutaciones

**Decisión**: Cada tarea muestra su estado (Pendiente/En progreso/Resuelta/Cancelada) con badge de color. Las transiciones se hacen con `useMutation` que invalida la query de lista.

**Alternativa considerada**: Optimistic updates con TanStack Query.
**Rechazada porque**: agrega complejidad innecesaria para un flujo que no es de alta frecuencia. La recarga tras mutación es aceptable y más simple.

### D6: Monitores con filtros como query params

**Decisión**: Los filtros de monitores (materia, regional, comisión, estado, fechas) se persisten como query params de la URL. TanStack Query reacciona a cambios de filtros.

**Racional**: Permite compartir URLs con filtros aplicados y navegación con back/forward del browser. Los query params son la fuente de verdad del estado de filtros.

### D7: Setup de cuatrimestre como wizard guiado

**Decisión**: FL-03 se implementa como un wizard multi-step con 7 pasos (crear cohorte → clonar equipo → ajustar asignaciones → ajustar vigencias → programas → fechas → aviso). Cada paso es un componente independiente.

**Racional**: El flujo es secuencial por naturaleza. Un wizard guía al usuario y previene pasos fuera de orden. Cada paso puede guardar parcialmente.

## Risks / Trade-offs

- **[Riesgo] Cambios de API en backends**: Los endpoints de C-08 a C-17 pueden evolucionar → **Mitigación**: Usar types compartidos y mapeo explícito en servicios; si la API cambia, solo se actualiza el servicio.
- **[Riesgo] Volumen de datos en monitores**: F2.7 puede devolver miles de registros → **Mitigación**: Paginación server-side con TanStack Query `useInfiniteQuery` y filtros obligatorios para acotar resultados.
- **[Trade-off] Complejidad del wizard de setup**: 7 pasos es largo → Se acepta porque FL-03 es un flujo poco frecuente (una vez por cuatrimestre) y el valor de guiar al usuario supera la complejidad.
- **[Trade-off] Duplicación de tipos**: Algunos tipos (Equipo, Aviso, Tarea) podrían repetirse entre C-22 y C-23 → Se acepta por ahora; si se detecta alta duplicación en C-24 se extraen a `shared/types/domain/`.

## Open Questions

<!-- No open questions at this stage. All decisions are resolved based on KB and existing patterns. -->
