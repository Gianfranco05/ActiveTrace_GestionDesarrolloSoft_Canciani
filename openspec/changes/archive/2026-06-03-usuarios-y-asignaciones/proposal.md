## Why

C-06 delivered the academic structure backbone (Carrera, Cohorte, Materia). C-04 delivered RBAC with Rol table and seed data. Now we need the **people layer** — who uses the system and how they're assigned to roles in the academic context.

Without C-07, there are no Usuarios (profile PII), no Asignaciones linking people to roles, and most critically **no roles in JWTs** — the `roles=[]` from C-03 remains empty. Every downstream change (C-08 equipos-docentes, C-09 padron, C-13 encuentros, etc.) needs both entities to exist AND roles to be populated in the auth flow.

The KB defines (E4) Usuario with PII encryption and (E5) Asignacion with temporal vigencia as the bridge between identity (AuthUser from C-03) and authorization (Rol from C-04).

## What Changes

- **Usuario ORM model** — 1:1 profile extension of AuthUser from C-03. PII fields (dni, cuil, cbu, alias_cbu) encrypted with AES-256-GCM. Business attributes: nombre, apellidos, legajo, legajo_profesional, regional, banco, facturador, estado. NO email (email lives in AuthUser only).
- **AES-256-GCM encryption layer** — encrypt on write, decrypt on read in the service layer. PII NEVER exposed in logs, API list responses, or error messages.
- **Asignacion ORM model** — links Usuario ↔ Rol ↔ Materia/Carrera/Cohorte/comisiones with temporal vigencia. Self-referential `responsable_id` for hierarchy. `estado_vigencia` is DERIVED (not stored).
- **RoleResolver service** — THE CRITICAL BRIDGE. Reads active Asignaciones for a user and resolves distinct rol_ids. Called by `auth_service.py` during login/refresh.
- **AuthService modification** — `_issue_tokens()` and `_create_temp_2fa_token()` now resolve actual roles from Asignaciones instead of `roles=[]`.
- **get_current_user enrichment** — UserSession.roles populated from resolved Asignaciones.
- **Pydantic safe + full response schemas** — UsuarioSafeResponse (no PII) for lists; UsuarioResponse (with PII) for detail views.
- **CRUD routers** — `/api/admin/usuarios` with `require_permission("usuarios:gestionar")`, `/api/asignaciones` with `require_permission("equipos:asignar")`.
- **Alembic migration 006** — creates `usuario`, `asignacion` tables with FKs, indexes, and encrypted columns.

## Capabilities

### New Capabilities
- `usuario-model`: Usuario ORM model + PII encryption (AES-256-GCM) + safe/full schemas
- `asignacion-model`: Asignacion ORM model + FK references + derived vigencia
- `role-resolver`: Role resolution service bridging Asignaciones → JWT claims
- `usuarios-admin-api`: CRUD endpoints for Usuario with PII-safe responses
- `asignaciones-api`: CRUD endpoints for Asignacion with temporal validation

### Modified Capabilities
- `backend/app/services/auth_service.py` — `_issue_tokens()` and `_create_temp_2fa_token()` enriched with resolved roles
- `backend/app/core/dependencies.py` — `get_current_user` now sees populated roles
- `backend/app/models/__init__.py` — export Usuario, Asignacion
- `backend/app/main.py` — register usuario and asignacion routers

## Impact

- **New model**: `backend/app/models/usuario.py`, `backend/app/models/asignacion.py`
- **New schemas**: `backend/app/schemas/usuario.py`, `backend/app/schemas/asignacion.py`
- **New repositories**: `backend/app/repositories/usuario_repository.py`, `backend/app/repositories/asignacion_repository.py`
- **New service**: `backend/app/services/role_resolver.py`, `backend/app/services/usuario_service.py`, `backend/app/services/asignacion_service.py`
- **New routers**: `backend/app/api/v1/routers/usuarios.py`, `backend/app/api/v1/routers/asignaciones.py`
- **Modified files**: `auth_service.py`, `dependencies.py`, `models/__init__.py`, `main.py`
- **New migration**: `backend/alembic/versions/006_usuarios_y_asignaciones.py`
- **Dependencies**: `C-06` (Carrera, Cohorte, Materia), `C-04` (Rol table), `C-03` (AuthUser 1:1), `C-02` (BaseModelMixin, AES-256, tenant scope)
