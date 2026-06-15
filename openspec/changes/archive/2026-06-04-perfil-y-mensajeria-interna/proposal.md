## Why

C-07 (usuarios-y-asignaciones) entregó el modelo Usuario con PII cifrada y C-03 (auth-jwt-2fa) entregó la autenticación completa con logout. C-04 (rbac-permisos-finos) estableció el guard `require_permission` como gate de autorización. Ahora C-20 cierra el ciclo de identidad del usuario dándole control sobre su propio perfil y habilita la mensajería interna entre usuarios registrados — el canal de comunicación asincrónica dentro del sistema, paralelo al sistema de emails a alumnos (Comunicacion en C-12).

Sin C-20, los usuarios no pueden editar sus datos bancarios, regional ni modalidad de cobro por sí mismos — toda modificación dependería de un ADMIN vía `/api/admin/usuarios`. La mensajería interna (FL-10) queda sin soporte, forzando a docentes y coordinación a usar canales externos para coordinación cotidiana.

## What Changes

- **GET/PUT `/api/perfil`** — endpoint para que cualquier usuario autenticado vea y edite su perfil. Campos editables: nombre, apellidos, dni, banco, cbu, alias_cbu, regional, legajo_profesional, facturador. CUIL es solo lectura (validado en servicio, rechazado si viene en el body). Email se lee de `auth_user` (no se edita por este endpoint).
- **GET `/api/inbox`** — listado de hilos de mensajes recibidos por el usuario autenticado, ordenados por última actividad descendente.
- **GET `/api/inbox/{thread_id}`** — detalle del hilo completo (mensaje raíz + todas las respuestas en orden cronológico).
- **POST `/api/inbox`** — enviar un nuevo mensaje a otro usuario (inicia un hilo nuevo).
- **POST `/api/inbox/{thread_id}/reply`** — responder dentro de un hilo existente.
- **Modelo Mensaje** — entidad para mensajería interna con parent_id auto-referencial que forma hilos.
- **Migración Alembic** — nueva migración para la tabla `mensaje`.
- **Seed de permisos** — `perfil:editar` y `mensajeria:usar` para todos los roles autenticados (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS).
- **Códigos de auditoría** — `PERFIL_EDITAR`, `MENSAJE_ENVIAR`.

## Capabilities

### New Capabilities
- `perfil`: Lectura y edición del perfil propio. GET devuelve todos los campos del Usuario (PII descifrada para el dueño). PUT actualiza campos editables; CUIL es inmutable desde este endpoint.
- `inbox-mensajeria`: Mensajería interna entre usuarios registrados. Envío de mensajes (inicia hilo), lectura de inbox (hilos recibidos), visualización de hilo completo, respuesta dentro del hilo.

### Modified Capabilities
- *(ninguna — C-20 introduce modelos, endpoints y permisos nuevos, no modifica specs existentes)*

## Impact

- **New model**: `backend/app/models/mensaje.py` — Mensaje con BaseModelMixin
- **New migration**: `backend/alembic/versions/<rev>_mensaje.py` — una migración para tabla mensaje
- **New repository**: `backend/app/repositories/mensaje_repository.py` — CRUD con queries de hilos
- **New services**: `backend/app/services/perfil_service.py`, `backend/app/services/mensaje_service.py`
- **New routers**: `backend/app/api/v1/routers/perfil.py` (prefix `/api/perfil`), `backend/app/api/v1/routers/inbox.py` (prefix `/api/inbox`)
- **New schemas**: `backend/app/schemas/perfil.py`, `backend/app/schemas/mensajes.py`
- **Modified files**: `backend/app/main.py` — registrar routers de perfil e inbox
- **Modified seed**: seed de permisos para `perfil:editar`, `mensajeria:usar`
- **Modified permissions**: `backend/app/core/permissions.py` — agregar `perfil:editar`, `mensajeria:usar`
- **Modified audit codes**: `backend/app/core/audit_codes.py` — agregar `PERFIL_EDITAR`, `MENSAJE_ENVIAR`
- **Dependencies**: `C-07` (Usuario model, auth_user model), `C-03` (logout reusado)
