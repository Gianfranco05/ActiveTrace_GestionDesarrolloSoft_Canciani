## 1. Rol Model — RED → GREEN → TRIANGULATE

- [x] 1.1 RED: Write failing test `test_rol_model.py` — `test_create_rol` expects UUID id, tenant_id, nombre, descripcion=None, timestamps
- [x] 1.2 GREEN: Implement `backend/app/models/rol.py` — Rol ORM with fields per D4, extends BaseModelMixin, UNIQUE(tenant_id, nombre)
- [x] 1.3 Execute tests: confirm GREEN
- [x] 1.4 TRIANGULATE: Add `test_rol_nombre_unique_per_tenant`, `test_rol_same_nombre_different_tenant_allowed`, `test_rol_soft_delete`
- [x] 1.5 Execute tests: confirm all pass
- [x] 1.6 REFACTOR: Ensure BaseModelMixin compatibility, extract Rol factory fixture

## 2. Permiso Model — RED → GREEN → TRIANGULATE

- [x] 2.1 RED: Write failing test `test_permiso_model.py` — `test_create_permiso` expects UUID id, codigo, descripcion
- [x] 2.2 GREEN: Implement `backend/app/models/permiso.py` — Permiso ORM with fields per D4 (NOT BaseModelMixin — standalone Base, NO tenant_id, NO soft delete)
- [x] 2.3 Execute tests: confirm GREEN
- [x] 2.4 TRIANGULATE: Add `test_permiso_codigo_unique`, `test_permiso_no_tenant_scope` (no tenant_id field)
- [x] 2.5 Execute tests: confirm all pass

## 3. RolPermiso Model — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test `test_rol_permiso_model.py` — `test_create_rol_permiso` expects UUID id, rol_id, permiso_id, UNIQUE(rol_id, permiso_id)
- [x] 3.2 GREEN: Implement `backend/app/models/rol_permiso.py` — RolPermiso ORM with fields per D4 (NOT BaseModelMixin — standalone Base, FK cascade)
- [x] 3.3 Execute tests: confirm GREEN
- [x] 3.4 TRIANGULATE: Add `test_duplicate_rol_permiso_rejected`, `test_rol_permiso_cascade_on_rol_delete`
- [x] 3.5 Execute tests: confirm all pass
- [x] 3.6 Update `backend/app/models/__init__.py` — export Rol, Permiso, RolPermiso

## 4. RbacRepository — RED → GREEN → TRIANGULATE

- [x] 4.1 RED: Write failing test `test_rbac_repository.py` — `test_get_effective_permissions` expects distinct permission codigos for given role names
- [x] 4.2 GREEN: Implement `backend/app/repositories/rbac_repository.py` — `RbacRepository` with `get_effective_permissions(db, role_names) -> set[str]`, `get_roles_by_tenant(db, tenant_id)`, `get_permisos_catalog(db)`, `assign_permisos_to_rol(db, rol_id, permiso_ids)`
- [x] 4.3 Execute tests: confirm GREEN
- [x] 4.4 TRIANGULATE: Add `test_empty_role_list_returns_empty`, `test_non_existent_role_returns_empty`, `test_get_roles_by_tenant_excludes_soft_deleted`, `test_assign_permisos_replace_all`
- [x] 4.5 Execute tests: confirm all pass

## 5. require_permission Guard — RED → GREEN → TRIANGULATE

- [x] 5.1 RED: Write failing test `test_require_permission.py` — `test_user_with_permission_passes` expects no exception raised
- [x] 5.2 GREEN: Implement `require_permission(codigo)` in `core/dependencies.py` — FastAPI dependency that calls get_current_user, queries effective permissions, returns 403 if missing
- [x] 5.3 Execute tests: confirm GREEN
- [x] 5.4 TRIANGULATE: Add `test_user_without_permission_gets_403`, `test_unauthenticated_gets_401_before_403`, `test_empty_roles_gets_403`, `test_require_permission_return_user`
- [x] 5.5 Execute tests: confirm all pass
- [x] 5.6 REFACTOR: Extract permission query helper, ensure consistent 403 response format

## 6. RBAC Schemas — Implementation

- [x] 6.1 Implement `schemas/rbac.py` — `RolCreate(nombre, descripcion?)`, `RolResponse(id, nombre, descripcion)`, `RolUpdate(nombre?, descripcion?)`, `RolWithPermisosResponse(id, nombre, descripcion, permisos)`, `PermisoCreate(codigo, descripcion?)`, `PermisoResponse(id, codigo, descripcion)`, `SetRolePermisosRequest(permiso_ids)`
- [x] 6.2 All schemas use `model_config = ConfigDict(extra='forbid')`

## 7. RBAC Router — RED → GREEN → TRIANGULATE

- [x] 7.1 RED: Write failing integration test `test_rbac_router.py` — `test_list_roles` GET /api/v1/rbac/roles returns tenant-scoped roles
- [x] 7.2 GREEN: Implement `backend/app/api/v1/routers/rbac.py` — CRUD endpoints per D6 with `require_permission("usuarios:gestionar")` guard
- [x] 7.3 Execute tests: confirm GREEN
- [x] 7.4 TRIANGULATE: Add `test_create_role`, `test_create_duplicate_role_409`, `test_get_role_with_permisos`, `test_set_role_permisos`, `test_list_permisos`, `test_create_permiso`, `test_rbac_without_permission_returns_403`
- [x] 7.5 Execute tests: confirm all pass

## 8. Alembic Migration 003 — RBAC Tables + Seed Data

- [x] 8.1 Create migration: `003_rbac.py` — creates rol, permiso, rol_permiso tables
- [x] 8.2 Add seed data: INSERT 7 roles per tenant (idempotent via NOT EXISTS subquery)
- [x] 8.3 Add seed data: INSERT all 21 permissions (idempotent via NOT EXISTS)
- [x] 8.4 Add seed data: INSERT all RolPermiso mappings per KB §3.3 matrix (NEXO = 0 permisos)
- [x] 8.5 Verify migration rolls forward and backward cleanly
- [x] 8.6 Update `alembic/env.py` — register new models for autogenerate

## 9. Integration and Matrix Verification

- [x] 9.1 Write `test_rbac_integration.py` — full RBAC flow: create role, assign permisos, verify, with multi-tenant isolation
- [x] 9.2 Write `test_create_role_inherits_no_permisos` — new role starts with empty permission set
- [x] 9.3 Execute full test suite: 140 tests pass

## 10. Documentation and Cleanup

- [x] 10.1 Update docstrings in `core/dependencies.py` marking `# C-04: require_permission` sections
- [x] 10.2 Run linting/type-checking on all new files — ruff: all checks passed
