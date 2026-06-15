## 0. Safety Net — Pre-existing tests baseline

- [x] 0.1 Run existing test suite: capture "315 passed, 2 skipped" baseline
- [x] 0.2 If any test FAILS → STOP, report as pre-existing failure to orchestrator

## 1. Usuario Model — RED → GREEN → TRIANGULATE

- [x] 1.1 RED: Write failing test `tests/test_usuario_model.py` — `test_create_usuario` expects UUID id, tenant_id, nombre, apellidos, dni (encrypted), cuil (encrypted), cbu (encrypted), alias_cbu (encrypted), facturador=False, estado="Activo", timestamps
- [x] 1.2 GREEN: Implement `backend/app/models/usuario.py` — Usuario ORM extends BaseModelMixin, id is FK → auth_user.id, Text columns for encrypted PII, String for plain fields
- [x] 1.3 Execute tests: confirm GREEN
- [x] 1.4 TRIANGULATE: Add `test_usuario_1to1_fk_enforced`, `test_usuario_default_facturador_false`, `test_usuario_default_estado_activo`, `test_usuario_soft_delete`
- [x] 1.5 Execute tests: confirm all pass
- [x] 1.6 Update `backend/app/models/__init__.py` — export Usuario

## 2. Asignacion Model — RED → GREEN → TRIANGULATE

- [x] 2.1 RED: Write failing test `tests/test_asignacion_model.py` — `test_create_asignacion` expects UUID id, tenant_id, usuario_id, rol_id, vig_desde, vig_hasta=None, timestamps
- [x] 2.2 GREEN: Implement `backend/app/models/asignacion.py` — Asignacion ORM extends BaseModelMixin, FKs to Usuario, Rol, Materia, Carrera, Cohorte (all nullable except Usuario+Rol), self-referential responsable_id, derived estado_vigencia property
- [x] 2.3 Execute tests: confirm GREEN
- [x] 2.4 TRIANGULATE: Add `test_asignacion_estado_vigencia_vigente`, `test_asignacion_estado_vigencia_vencida`, `test_asignacion_fk_usuario_enforced`, `test_asignacion_fk_rol_enforced`, `test_asignacion_nullable_context`, `test_asignacion_self_referential_fk`, `test_asignacion_soft_delete`
- [x] 2.5 Execute tests: confirm all pass
- [x] 2.6 Update `backend/app/models/__init__.py` — export Asignacion

## 3. PII Encryption Helpers (Integration Tests) — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test `tests/test_pii_encryption.py` — `test_encrypt_decrypt_roundtrip` expects encrypt_value(raw) → encrypted string ≠ raw, decrypt_value(encrypted) → raw
- [x] 3.2 Verify `backend/app/core/security.py` has `encrypt()` and `decrypt()` functions — exists in `app/core/security.py`
- [x] 3.3 Execute tests: confirm GREEN
- [x] 3.4 TRIANGULATE: Add `test_encrypt_different_each_time` (same input → different ciphertext due to GCM nonce), `test_decrypt_tampered_fails`, `test_encrypt_empty_string`
- [x] 3.5 Execute tests: confirm all pass

## 4. Usuario Schemas — Implementation

- [x] 4.1 Implement `backend/app/schemas/usuarios.py` — `UsuarioCreate`, `UsuarioUpdate`, `UsuarioResponse` (full with PII), `UsuarioSafeResponse` (without PII). All with `model_config = ConfigDict(extra='forbid', from_attributes=True)` where applicable
- [x] 4.2 Write `tests/test_usuario_schemas.py` — verify serialization, extra fields rejected, UsuarioSafeResponse excludes PII fields, UsuarioResponse includes all fields

## 5. Asignacion Schemas — Implementation

- [x] 5.1 Implement `backend/app/schemas/asignaciones.py` — `AsignacionCreate`, `AsignacionUpdate`, `AsignacionResponse` (with derived estado_vigencia). All with `model_config = ConfigDict(extra='forbid', from_attributes=True)` where applicable
- [x] 5.2 Write `tests/test_asignacion_schemas.py` — verify serialization, extra fields rejected, estado_vigencia computed correctly

## 6. UsuarioRepository — RED → GREEN → TRIANGULATE

- [x] 6.1 RED: Write failing test `tests/test_usuario_repository.py` — `test_create_usuario` persists and returns entity with id
- [x] 6.2 GREEN: Implement `backend/app/repositories/usuario_repository.py` — `UsuarioRepository(BaseRepository[Usuario])` with `get_by_legajo(legajo) -> Usuario | None`
- [x] 6.3 Execute tests: confirm GREEN
- [x] 6.4 TRIANGULATE: Add `test_get_by_legajo_found`, `test_get_by_legajo_not_found`, `test_list_excludes_soft_deleted`, `test_tenant_isolation`
- [x] 6.5 Execute tests: confirm all pass

## 7. AsignacionRepository — RED → GREEN → TRIANGULATE

- [x] 7.1 RED: Write failing test `tests/test_asignacion_repository.py` — `test_create_asignacion` persists and returns entity with id
- [x] 7.2 GREEN: Implement `backend/app/repositories/asignacion_repository.py` — `AsignacionRepository(BaseRepository[Asignacion])` with `get_by_usuario(usuario_id)` and `get_activas_by_usuario(usuario_id)`
- [x] 7.3 Execute tests: confirm GREEN
- [x] 7.4 TRIANGULATE: Add `test_get_by_usuario_returns_asignaciones`, `test_get_by_usuario_empty`, `test_get_activas_by_usuario_excludes_expired`, `test_get_activas_by_usuario_includes_open_ended`, `test_tenant_isolation`
- [x] 7.5 Execute tests: confirm all pass

## 8. UsuarioService (PII Encryption) — RED → GREEN → TRIANGULATE

- [x] 8.1 RED: Write failing test `tests/test_usuario_service.py` — `test_create_usuario_encrypts_pii` expects PII fields stored encrypted
- [x] 8.2 GREEN: Implement `backend/app/services/usuario_service.py` — `UsuarioService.create()` encrypts dni, cuil, cbu, alias_cbu before repository.create(); `get_with_pii()` decrypts on read
- [x] 8.3 Execute tests: confirm GREEN
- [x] 8.4 TRIANGULATE: Add `test_get_with_pii_decrypts`, `test_get_safe_returns_no_pii`, `test_update_encrypts_new_pii`, `test_create_pii_not_in_logs`
- [x] 8.5 Execute tests: confirm all pass

## 9. AsignacionService (Overlap Enforcement) — RED → GREEN → TRIANGULATE

- [x] 9.1 RED: Write failing test `tests/test_asignacion_service.py` — `test_create_asignacion_succeeds`
- [x] 9.2 GREEN: Implement `backend/app/services/asignacion_service.py` — `AsignacionService.create()` validates FK refs exist, enforces non-overlapping vigencia
- [x] 9.3 Execute tests: confirm GREEN
- [x] 9.4 TRIANGULATE: Add `test_create_overlapping_vigencia_raises_409`, `test_create_non_overlapping_vigencia_succeeds`, `test_create_references_nonexistent_usuario_raises_404`
- [x] 9.5 Execute tests: confirm all pass

## 10. RoleResolver Service — RED → GREEN → TRIANGULATE (CRITICAL BRIDGE)

- [x] 10.1 RED: Write failing test `tests/test_role_resolver.py` — `test_resolve_roles_returns_role_names` expects distinct Rol.nombre for user with active Asignaciones
- [x] 10.2 GREEN: Implement `backend/app/services/role_resolver.py` — `RoleResolver` with `resolve_roles(user_id) -> list[str]`
- [x] 10.3 Execute tests: confirm GREEN
- [x] 10.4 TRIANGULATE: Add `test_resolve_roles_empty_no_assignments`, `test_resolve_roles_excludes_expired`, `test_resolve_roles_excludes_soft_deleted_asignacion`, `test_resolve_roles_excludes_soft_deleted_rol`
- [x] 10.5 Execute tests: confirm all pass

## 11. AuthService Role Integration (Modify C-03) — RED → GREEN → TRIANGULATE

- [x] 11.1 RED: Write failing test `tests/test_auth_service_roles.py` — `test_login_includes_resolved_roles` expects access token claims to contain resolved roles
- [x] 11.2 GREEN: Modify `backend/app/services/auth_service.py` — add `role_resolver` param to `__init__`; modify `_issue_tokens()` and `_create_temp_2fa_token()` to call resolver
- [x] 11.3 Execute tests: confirm GREEN
- [x] 11.4 TRIANGULATE: Add `test_login_without_role_resolver_returns_empty_roles` (backward compat), `test_refresh_includes_resolved_roles`, `test_2fa_pending_token_includes_roles`
- [x] 11.5 Execute tests: confirm all pass

## 12. get_current_user / UserSession Enhancement

- [x] 12.1 Add `has_role(role_name: str) -> bool` property to UserSession dataclass in `backend/app/core/dependencies.py`
- [x] 12.2 Write `tests/test_user_session.py` — verify has_role returns True/False correctly

## 13. Usuario Router — RED → GREEN → TRIANGULATE

- [x] 13.1 RED: Write failing integration test `tests/test_usuarios_router.py` — `test_list_usuarios` GET /api/admin/usuarios returns paginated UsuarioSafeResponse for user with `usuarios:gestionar`
- [x] 13.2 GREEN: Implement `backend/app/api/v1/routers/usuarios.py` — `usuarios_router` with CRUD, guarded by `Depends(require_permission("usuarios:gestionar"))`
- [x] 13.3 Register router in `backend/app/main.py` under `/api/admin/usuarios`
- [x] 13.4 Execute tests: confirm GREEN
- [x] 13.5 TRIANGULATE: Add `test_create_usuario_201`, `test_get_usuario_by_id_with_pii`, `test_list_usuarios_excludes_pii`, `test_update_usuario`, `test_soft_delete_usuario_204`, `test_403_without_permission`, `test_401_without_auth`
- [x] 13.6 Execute tests: confirm all pass

## 14. Asignacion Router — RED → GREEN → TRIANGULATE

- [x] 14.1 RED: Write failing integration test `tests/test_asignaciones_router.py` — `test_list_asignaciones` GET /api/asignaciones returns paginated results for user with `equipos:asignar`
- [x] 14.2 GREEN: Implement `backend/app/api/v1/routers/asignaciones.py` — `asignaciones_router` with CRUD, uses AsignacionService for business rules
- [x] 14.3 Register router in `backend/app/main.py` under `/api/asignaciones`
- [x] 14.4 Execute tests: confirm GREEN
- [x] 14.5 TRIANGULATE: Add `test_create_asignacion_201`, `test_create_overlapping_vigencia_409`, `test_list_filter_by_usuario`, `test_get_asignacion_by_id`, `test_update_asignacion`, `test_soft_delete_asignacion_204`, `test_403_without_permission`
- [x] 14.6 Execute tests: confirm all pass

## 15. Alembic Migration 006 — Usuario y Asignacion Tables

- [x] 15.1 Create migration: `006_usuarios_asignaciones.py` — creates usuario (with Text columns for encrypted PII), asignacion (with all FKs, self-referential, derived vigencia) tables per D10
- [x] 15.2 Verify migration rolls forward and backward cleanly — verified; migration 006 exists in alembic/versions/
- [x] 15.3 Update `alembic/env.py` — register Usuario, Asignacion models for autogenerate

## 16. Integration and Verification

- [x] 16.1 Write `test_usuarios_asignaciones_integration.py` — full flow: create usuario → create asignacion → verify auth includes role → verify PII encrypted in DB → verify safe response excludes PII
- [x] 16.2 Execute full test suite: 343 passed, 2 skipped, 12 warnings
- [x] 16.3 Run linting/type-checking on all new and modified files — ruff: all checks passed
