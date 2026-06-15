## Context

El backend de activia-trace ya expone los endpoints necesarios para las funcionalidades de FINANZAS y ADMIN:

- **C-06 (estructura-academica)**: CRUD de carreras, cohortes, materias con endpoints REST bajo `/api/estructura/`
- **C-07 (usuarios-y-asignaciones)**: ABM de usuarios del tenant con endpoints bajo `/api/usuarios/`
- **C-18 (liquidaciones-honorarios)**: Cálculo, cierre, historial de liquidaciones, grilla salarial (SalarioBase, SalarioPlus), gestión de facturas bajo `/api/liquidaciones/`
- **C-19 (panel-auditoria)**: Métricas de interacciones y log completo de auditoría bajo `/api/auditoria/`

El frontend ya tiene la shell completa: `AppLayout` con Sidebar/Topbar, `ProtectedRoute` con auth JWT, `RequirePermission` con RBAC fino, TanStack Query v5 instalado, React Hook Form + Zod para formularios, Tailwind CSS para estilos, y el cliente API con interceptor de auth + refresh automático.

Este change construye las vistas que consumen esos endpoints, sin tocar el backend.

## Goals / Non-Goals

**Goals:**
- Implementar dos feature modules: `features/finanzas/` y `features/admin/`
- Construir 8 páginas con sus componentes, hooks, servicios y tipos asociados
- Integrar con el sistema de permisos RBAC existente (`RequirePermission`)
- Mostrar KPIs y segmentación en la vista de liquidaciones
- Soportar upload de archivos PDF para facturas
- Cubrir con tests unitarios los flujos críticos

**Non-Goals:**
- No modificar el backend ni sus endpoints
- No modificar el sistema de auth, RBAC, ni el layout existente
- No implementar E2E tests (playwright) — solo unitarios con vitest
- No rediseñar los NAV_ITEMS existentes — solo agregar nuevas entradas

## Decisions

### D1: Dos feature modules separados (`features/finanzas/` y `features/admin/`)

**Rationale**: Las funcionalidades de FINANZAS y ADMIN son dominios distintos con permisos, actores y flujos independientes. Mantenerlos separados sigue el patrón feature-based ya establecido por `features/auth/` y `features/dashboard/`. Una sola feature `features/admin` que incluya finanzas violaría la separación de concerns.

**Alternativa considerada**: Un solo módulo `features/admin-finanzas/` — rechazado porque mezcla dos dominios con modelos de datos y permisos disjuntos.

### D2: Estructura de cada feature con subdirectorios estándar

Cada feature sigue la estructura canónica del proyecto:

```
features/<name>/
├── components/   # Componentes presentacionales y de layout interno
├── hooks/        # Custom hooks con TanStack Query (useQuery, useMutation)
├── pages/        # Page components (route-level)
├── services/     # Funciones que llaman a api.get/post/put/delete
└── types/        # Interfaces y tipos Zod
```

### D3: TanStack Query para todo fetching y mutación

Todo fetch de datos usa `useQuery` con keys tipadas. Toda mutación usa `useMutation` con `onSuccess` para invalidar queries relacionadas. Los hooks encapsulan la lógica de caché, loading y error states.

**Alternativa considerada**: Fetch manual con useEffect — rechazado porque TanStack Query ya está en el stack y maneja caché, re-fetch, loading/error states y retry automático.

### D4: React Hook Form + Zod para formularios ABM

Los formularios de creación/edición (grilla salarial, estructura académica, usuarios, facturas) usan `useForm` con `zodResolver`. Los schemas Zod garantizan validación tipada en build-time.

### D5: Guards de permisos a nivel ruta y a nivel acción

- **Ruta**: cada page está wrappeada en `<RequirePermission requiredPermission="modulo:accion" />`
- **Acción**: botones de cerrar liquidación, cambiar estado de factura, etc. verifican permiso con `hasPermission()` del hook `useAuth`
- **Nav**: NAV_ITEMS usa `permission` para filtrar visibilidad (patrón ya implementado en Sidebar)

### D6: File upload para facturas

El upload del PDF de factura usa `FormData` con `<input type="file" accept=".pdf">`. El endpoint espera `multipart/form-data`. Se muestra preview del nombre y tamaño antes de submit.

### D7: Segmentación de liquidaciones con tabs

La vista de liquidaciones usa tabs o segmentos visuales (General | NEXO | Factura) para la separación contable definida en F10.6. Cada segmento es una tabla independiente con sus propios totales.

## Risks / Trade-offs

- **[R1] Dependencia de C-18 endpoints liquidaciones**: Si los endpoints de liquidaciones cambian su contrato, el frontend debe adaptarse. → Mitigación: tipos TypeScript en `features/finanzas/types/` que reflejan el contrato actual; si el backend cambia, los tipos no compilan y el error es visible en build-time.
- **[R2] Performance en log de auditoría**: El log completo puede tener miles de registros. → Mitigación: paginación server-side con TanStack Query `useInfiniteQuery`; filtros aplicados como query params.
- **[R3] Upload de archivos grandes**: Facturas PDF pueden exceder el límite del servidor. → Mitigación: validación client-side de tamaño máximo (10 MB) con mensaje de error claro; el backend ya debe tener su propia validación.
- **[R4] Complejidad de la grilla salarial**: Dos tablas (SalarioBase, SalarioPlus) con vigencias solapadas pueden confundir al usuario. → Mitigación: UI con validación visual de solapamiento (highlight de filas con conflicto de fechas).

## Open Questions

- **Q1**: ¿Los endpoints de C-18 ya devuelven los KPIs calculados o el frontend debe calcularlos a partir de los datos de la tabla? → Asumir que el backend devuelve los totales. Si no, el frontend los calcula con `useMemo`.
- **Q2**: ¿El historial de liquidaciones es una tabla plana o requiere drill-down por docente? → Por simplicidad inicial, tabla plana. Si se requiere drill-down, se agrega en iteración posterior.
- **Q3**: ¿El panel de auditoría requiere gráficos (charts) o solo tablas/metrics numéricas? → Tablas y métricas numéricas. Los gráficos son deseables pero no bloqueantes; se pueden agregar con Recharts en iteración futura.
