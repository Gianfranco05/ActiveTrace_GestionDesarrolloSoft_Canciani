## Why

Los roles FINANZAS y ADMIN no tienen interfaz en el frontend para ejecutar sus funciones críticas: liquidar honorarios docentes con segmentación NEXO/factura, gestionar la grilla salarial, administrar la estructura académica, los usuarios del tenant y supervisar la actividad del sistema mediante auditoría. El backend ya expone estos endpoints (C-06 estructura, C-07 usuarios, C-18 liquidaciones, C-19 auditoría). Este change construye las vistas que consumen esos endpoints, completando el frontend para los roles administrativos y financieros.

## What Changes

- **Nuevo feature module `features/finanzas/`**: LiquidacionesPage (vista segmentada general/NEXO/factura + KPIs), HistorialLiquidacionesPage, GrillaSalarialPage (ABM SalarioBase + SalarioPlus), FacturasPage (carga, estado, archivo adjunto)
- **Nuevo feature module `features/admin/`**: EstructuraAcademicaPage (ABM carreras, cohortes, materias), UsuariosPage (ABM usuarios tenant), PanelAuditoriaPage (métricas e interacciones), LogAuditoriaPage (log completo con filtros)
- **Rutas protegidas** en App.tsx con `RequirePermission` usando los permisos del backend: `liquidaciones:ver`, `liquidaciones:cerrar`, `liquidaciones:configurar-salarios`, `facturas:gestionar`, `estructura:gestionar`, `usuarios:gestionar`, `auditoria:ver`
- **Nuevas entradas en NAV_ITEMS** para Finanzas y Administracion, visibles solo con los permisos correspondientes
- **Servicios API** por feature consumiendo endpoints de C-06, C-07, C-18, C-19 via `@/shared/services/api`
- **Tests** con vitest + @testing-library/react cubriendo renderizado segmentado de liquidaciones, flujo de cierre, ABM de grilla salarial, panel de auditoria con filtros

## Capabilities

### New Capabilities

- `finanzas-liquidaciones`: Vista segmentada (general / NEXO / factura) con KPIs de cabecera, cierre de liquidacion que inmutabiliza el periodo, e historial de liquidaciones cerradas. Consume endpoints de C-18.
- `finanzas-grilla-salarial`: ABM de SalarioBase por rol y SalarioPlus por grupo/rol, ambos con vigencia temporal (desde/hasta). Consume endpoints de C-18.
- `finanzas-facturas`: Carga de facturas de docentes monotributistas con archivo adjunto (PDF), cambio de estado pendiente/abonada, filtros por docente y periodo. Consume endpoints de C-18.
- `admin-estructura-academica`: ABM de carreras, cohortes y materias del tenant. Consume endpoints de C-06.
- `admin-usuarios`: ABM de usuarios del tenant con asignacion de roles, activacion/desactivacion. Consume endpoints de C-07.
- `admin-auditoria`: Panel de metricas (acciones por dia, estado de comunicaciones, interacciones por docente y materia) + log completo de auditoria con filtros. Consume endpoints de C-19.

### Modified Capabilities

<!-- None: all capabilities are new frontend views for existing backend endpoints -->

## Impact

- **App.tsx**: nuevas rutas bajo AppLayout con RequirePermission
- **NAV_ITEMS**: nuevas entradas para Finanzas y Administracion
- **features/finanzas/**: nuevo modulo con pages, components, hooks, services, types
- **features/admin/**: nuevo modulo con pages, components, hooks, services, types
- **Dependencias backend**: C-06 (estructura academica endpoints), C-07 (usuarios endpoints), C-18 (liquidaciones, grilla salarial, facturas endpoints), C-19 (panel auditoria endpoints)
- **Sin impacto en**: auth, dashboard, ni features existentes
