# Design: Fixes críticos para experiencia ADMIN

## Fix 1 — URL de usuarios

**Problema**: `usuario.service.ts` llama a `/usuarios/` pero el backend expone en `/api/v1/admin/usuarios`.

**Solución**: Cambiar `BASE` en `usuario.service.ts` de `/usuarios` a `/v1/admin/usuarios`. Verificar también el interceptor HTTP — si la base ya incluye `/api`, la URL final debe ser `/api/v1/admin/usuarios`.

**Archivos**: `frontend/src/features/admin/services/usuario.service.ts`

---

## Fix 2 — Toggle estado usuarios

**Problema**: El frontend (`UsuariosPage.tsx`) llama `PATCH /usuarios/{id}/estado` pero el backend no tiene ese endpoint. En estructura académica sí existe (`PATCH /carreras/{id}/estado`, etc.).

**Solución**: Agregar en `backend/app/api/v1/routers/usuarios.py`:
```python
@router.patch("/{usuario_id}/estado", response_model=UsuarioResponse)
async def toggle_estado_usuario(usuario_id: UUID, body: EstadoToggleRequest, ...):
```
El body acepta `{"estado": "Activa"}` o `{"estado": "Inactiva"}` (mismo patrón que estructura).

**Archivos**: `backend/app/api/v1/routers/usuarios.py`

---

## Fix 3 — Sincronizar permisos del menú

**Problema**: `App.tsx` y `nav.ts` usan `equipos:ver`, `encuentros:ver`, `coloquios:ver`, `tareas:ver` para proteger rutas y mostrar items. Pero esos permisos NO existen en el catálogo — los reales son `equipos:asignar`, `encuentros:gestionar`, `coloquios:gestionar`, `tareas:gestionar`. El ADMIN tiene estos últimos, pero el frontend no lo reconoce.

**Solución**: Buscar y reemplazar en `App.tsx` y `nav.ts`:
- `equipos:ver` → `equipos:asignar`
- `encuentros:ver` → `encuentros:gestionar`
- `coloquios:ver` → `coloquios:gestionar`
- `tareas:ver` → `tareas:gestionar`

Si existe también `monitores:ver`, evaluar si corresponde a `atrasados:ver` o crear un alias.

**Archivos**: `frontend/src/App.tsx`, `frontend/src/shared/components/nav.ts`

---

## Fix 4 — Agregar items faltantes al sidebar

**Problema**: El sidebar no muestra Usuarios, Log de Auditoría, Finanzas, Coloquios, Tareas ni Avisos para el ADMIN. El admin tiene que adivinar URLs.

**Solución**: Agregar al `NAV_ITEMS` en `nav.ts` los items faltantes bajo sus secciones correspondientes:

| Item | Sección | Ruta | Permiso |
|------|---------|------|---------|
| Usuarios | Administración | `/admin/usuarios` | `usuarios:gestionar` |
| Log Auditoría | Administración | `/admin/auditoria/log` | `auditoria:ver` |
| Finanzas | Finanzas | `/finanzas` | `liquidaciones:ver` |
| Coloquios | Coordinación | `/coordinacion/coloquios` | `coloquios:gestionar` |
| Tareas | Coordinación | `/coordinacion/tareas` | `tareas:gestionar` |
| Avisos | Coordinación | `/coordinacion/avisos` | `avisos:publicar` |

**Archivos**: `frontend/src/shared/components/nav.ts`

---

## Fix 5 — Reset password admin-driven

**Problema**: Solo existe `POST /api/auth/forgot` + `POST /api/auth/reset` (flujo self-service). El admin no puede resetear la contraseña de otro usuario.

**Solución**: Agregar endpoint `POST /api/v1/admin/usuarios/{usuario_id}/reset-password` que:
1. Recibe `{"new_password": "..."}` (body con la nueva contraseña)
2. Hashea con Argon2id
3. Actualiza `auth_user.hashed_password`
4. Requiere `usuarios:gestionar`
5. Genera audit `USUARIO_PASSWORD_RESETEAR` con actor = admin, target = usuario

**Archivos**: `backend/app/api/v1/routers/usuarios.py`, `backend/app/schemas/usuarios.py`

---

## Fix 6 — Dashboard con datos por rol

**Problema**: `DashboardPage.tsx` muestra 4 cards con "—". Mismo dashboard para todos los roles.

**Solución**: Condicionar las métricas según `roles` del usuario (desde `useAuth`):

| Rol | Métricas |
|-----|----------|
| ADMIN | Total usuarios, asignaciones activas, últimas 5 acciones de auditoría, estado de comunicaciones |
| PROFESOR | Mis materias, alumnos atrasados, comunicaciones pendientes, próximos encuentros |
| ALUMNO | Mi estado académico, avisos sin leer, próximos coloquios, mensajes sin leer |

Para el MVP, implementar solo ADMIN + un fallback genérico para otros roles. Conectar a endpoints existentes (`/api/v1/admin/usuarios?limit=1`, `/api/auditoria/panel`, etc.).

**Archivos**: `frontend/src/features/shared/pages/DashboardPage.tsx`
