# Proposal: Fixes críticos para experiencia ADMIN

## What

6 fixes que desbloquean la experiencia del ADMIN en el frontend. El backend expone ~80 endpoints accesibles para ADMIN, pero el frontend bloquea el acceso por URLs rotas, permisos desincronizados, navegación incompleta y funcionalidades faltantes.

## Why

Un ADMIN recién creado (vía bootstrap) puede loguearse pero:
1. **No puede gestionar usuarios** — la página da 404 (URL mismatch frontend↔backend)
2. **No puede desactivar usuarios** — el endpoint de toggle estado no existe
3. **No ve 4 módulos en el menú** — permisos del frontend distintos a los del backend
4. **No puede navegar a Finanzas, Tareas, Coloquios, Avisos** — faltan en el sidebar
5. **No puede resetear contraseñas** de otros usuarios
6. **El dashboard no muestra datos** — mismo placeholder para todos los roles

## Fixes (ordenados por prioridad)

| # | Fix | Capa | Bloqueante |
|---|-----|------|:---:|
| 1 | Corregir URL de usuarios en frontend | Frontend | 🔴 |
| 2 | Agregar `PATCH /v1/admin/usuarios/{id}/estado` en backend | Backend | 🔴 |
| 3 | Sincronizar permisos del menú (App.tsx + nav.ts) | Frontend | 🔴 |
| 4 | Agregar items faltantes al sidebar (nav.ts) | Frontend | 🟡 |
| 5 | Agregar reset de password admin-driven | Backend | 🟡 |
| 6 | Dashboard con datos reales por rol | Frontend | 🟡 |

## Governance

**MEDIO** — modifica lógica de navegación y endpoints de usuarios. No toca auth, tenancy ni RBAC core.
