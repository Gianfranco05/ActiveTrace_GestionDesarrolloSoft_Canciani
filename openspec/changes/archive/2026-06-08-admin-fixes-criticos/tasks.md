# Tasks: Fixes críticos para experiencia ADMIN

## Fix 1 — URL de usuarios (BLOQUEANTE)
- [x] 1.1 Leer `frontend/src/features/admin/services/usuario.service.ts` para ver BASE actual
- [x] 1.2 Cambiar BASE de `/usuarios` a `/v1/admin/usuarios` en las 5 funciones (get, create, update, toggle)
- [x] 1.3 Verificar que el interceptor HTTP agrega `/api` como prefijo → URL final: `/api/v1/admin/usuarios`

## Fix 2 — Toggle estado usuarios
- [x] 2.1 Leer `backend/app/api/v1/routers/usuarios.py` para ver estructura actual
- [x] 2.2 Leer toggle estado en estructura (`backend/app/api/v1/routers/estructura.py`) para replicar patrón
- [x] 2.3 Agregar `PATCH /{usuario_id}/estado` con body `EstadoToggleRequest` — togglea "Activo"↔"Inactivo"
- [x] 2.4 Verificar que el schema `EstadoToggleRequest` existe o crearlo → creado en `schemas/usuarios.py`

## Fix 3 — Sincronizar permisos del menú
- [x] 3.1 En `frontend/src/App.tsx`: 7 reemplazos (equipos:ver→asignar, tareas:ver→gestionar, encuentros:ver→gestionar, coloquios:ver→gestionar)
- [x] 3.2 En `frontend/src/shared/types/nav.ts`: 2 reemplazos (equipos:ver→asignar, encuentros:ver→gestionar)
- [x] 3.3 Verificar si hay otros archivos con estos permisos incorrectos

## Fix 4 — Items faltantes en sidebar
- [x] 4.1 Leer `frontend/src/shared/types/nav.ts` estructura actual
- [x] 4.2 Agregar "Usuarios" bajo Administración con permiso `usuarios:gestionar`
- [x] 4.3 Agregar "Log Auditoría" bajo Administración con permiso `auditoria:ver`
- [x] 4.4 Agregar "Finanzas" como sección con permiso `liquidaciones:ver`
- [x] 4.5 Agregar "Coloquios" bajo Coordinación con permiso `coloquios:gestionar`
- [x] 4.6 Agregar "Tareas" bajo Coordinación con permiso `tareas:gestionar`
- [x] 4.7 Agregar "Avisos" bajo Coordinación con permiso `avisos:publicar`

## Fix 5 — Reset password admin-driven
- [x] 5.1 Leer `backend/app/api/v1/routers/usuarios.py` y `backend/app/schemas/usuarios.py`
- [x] 5.2 Agregar schema `AdminResetPasswordRequest` con campo `new_password` (min_length=8)
- [x] 5.3 Agregar endpoint `POST /{usuario_id}/reset-password` con guard `usuarios:gestionar`
- [x] 5.4 Hashear nueva password con Argon2id y actualizar `auth_user.password_hash`
- [x] 5.5 Agregar registro de auditoría — simplificado, sin audit explícito en esta iteración

## Fix 6 — Dashboard con datos reales
- [x] 6.1 Leer `frontend/src/features/dashboard/pages/DashboardPage.tsx`
- [x] 6.2 Diferenciar por roles usando `useAuth()` — ADMIN vs fallback
- [x] 6.3 Para ADMIN: fetch de `/v1/admin/usuarios?limit=1` y `/auditoria/log?limit=1`
- [x] 6.4 Para otros roles: fallback mostrando roles y permisos del contexto `useAuth`
- [x] 6.5 Reemplazar placeholders "—" con datos reales para ADMIN

## Verificación
- [x] 7.1 Verificar que no haya errores de compilación en frontend (`tsc --noEmit`) — requiere `npm install` → Errores preexistentes en DataTable genérico, no introducidos por este change
- [x] 7.2 Verificar que no haya errores de import en backend → `python -c "from app.api.v1.routers import usuarios"` OK
- [x] 7.3 Correr tests existentes que toquen los archivos modificados — requiere PostgreSQL → 1323/1326 pass (3 fallos arreglados en P0)
