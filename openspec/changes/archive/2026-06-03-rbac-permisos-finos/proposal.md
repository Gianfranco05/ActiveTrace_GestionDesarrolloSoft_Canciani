## Why

C-03 established authentication (who you are) but without authorization (what you can do) the system is not usable: every authenticated user has identical capabilities. C-04 delivers the fine-grained RBAC layer that maps roles to atomic permissions (`modulo:accion`), seeds the complete permission matrix from the domain model, and provides the `require_permission` guard that every downstream endpoint depends on. Without C-04, no change from C-06 onwards can protect its endpoints.

This is governance **CRITICO** — the permission model is the authorization backbone of the system.

## What Changes

- **Rol model** — named role with description. Seeds: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS
- **Permiso model** — atomic permission with `codigo` (`modulo:accion`) and description. Seeds: the full matrix from KB §3.3 (~20 permissions)
- **RolPermiso model** — many-to-many relationship between Rol and Permiso
- **`require_permission(codigo)` guard** — FastAPI dependency that resolves user's roles from the JWT (via `UserSession.roles` from C-03), queries the RolPermiso matrix server-side, and returns 403 if the required permission is not found
- **RBAC admin CRUD** — endpoints to list, create, update roles and permissions (ADMIN only)
- **Alembic migration 003** — creates `rol`, `permiso`, `rol_permiso` tables and seeds all roles + permissions + role-permission mappings
- **PermissionRepository** — queries the RolPermiso join for effective permissions given a list of role IDs

Key constraint: permissions are NOT cached in the JWT. The JWT carries `roles` (list of role names) but effective permissions are resolved server-side per request. This is intentional (D1).

## Capabilities

### New Capabilities

- `rbac-models`: Rol, Permiso, and RolPermiso ORM models with repositories
- `require-permission`: FastAPI dependency `require_permission(codigo)` that checks effective permissions against the RolPermiso matrix, returning 403 if denied
- `rbac-seed`: Seed data for all 7 roles, all permissions from the KB matrix, and their mappings in migration 003
- `rbac-catalog`: CRUD admin endpoints to list, create, update roles and permissions

### Modified Capabilities

- *(none — all capabilities are new)*

## Impact

- **Models**: `backend/app/models/rol.py` — Rol ORM model
- **Models**: `backend/app/models/permiso.py` — Permiso ORM model
- **Models**: `backend/app/models/rol_permiso.py` — RolPermiso association model
- **Core**: `backend/app/core/dependencies.py` — ADD `require_permission(codigo)` guard alongside existing `get_current_user`
- **Routers**: `backend/app/api/v1/routers/rbac.py` — CRUD endpoints for roles/permisos (ADMIN only)
- **Schemas**: `backend/app/schemas/rbac.py` — Request/response Pydantic schemas
- **Services**: `backend/app/services/rbac_service.py` — Permission resolution logic
- **Repositories**: `backend/app/repositories/rbac_repository.py` — RolRepository, PermisoRepository, RolPermisoRepository queries
- **Migration**: `backend/alembic/versions/003_rbac.py` — creates rol, permiso, rol_permiso tables + seed data
- **Models**: `backend/app/models/__init__.py` — export new models
