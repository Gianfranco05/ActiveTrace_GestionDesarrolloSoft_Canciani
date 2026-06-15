## 1. AuditAction Enum — Implementation

- [x] 1.1 Implement `backend/app/core/audit_codes.py` — `AuditAction(str, Enum)` with 7 codes: CALIFICACIONES_IMPORTAR, PADRON_CARGAR, COMUNICACION_ENVIAR, ASIGNACION_MODIFICAR, LIQUIDACION_CERRAR, IMPERSONACION_INICIAR, IMPERSONACION_FINALIZAR
- [x] 1.2 Write `tests/test_audit_codes.py` — verify all members, value==name, iteration, ValueError on invalid

## 2. AuditLog Model — RED → GREEN → TRIANGULATE

- [x] 2.1 RED: Write failing test `test_audit_log_model.py` — `test_create_audit_log` expects UUID id, tenant_id, actor_id, accion, optional fields
- [x] 2.2 GREEN: Implement `backend/app/models/audit_log.py` — AuditLog ORM per D8 (NOT BaseModelMixin)
- [x] 2.3 Execute tests: confirm GREEN
- [x] 2.4 TRIANGULATE: Add `test_no_updated_at_deleted_at`, `test_default_filas_afectadas`, `test_fk_constraints_rejected`, `test_tenant_indexed`
- [x] 2.5 Execute tests: confirm all pass
- [x] 2.6 Update `backend/app/models/__init__.py` — export AuditLog

## 3. AuditLog Repository — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test `test_audit_repository.py` — `test_create_audit_log` persists and returns entry with id
- [x] 3.2 GREEN: Implement `backend/app/repositories/audit_repository.py` — `AuditLogRepository` with `create()`, `list(filterable)`, `find_by_id()`; NO update/delete methods
- [x] 3.3 Execute tests: confirm GREEN
- [x] 3.4 TRIANGULATE: Add `test_list_empty`, `test_list_filter_by_accion`, `test_list_filter_by_actor_id`, `test_list_filter_by_date_range`, `test_list_tenant_isolation`, `test_list_default_pagination`, `test_find_by_id_returns_none_for_wrong_tenant`, `test_find_by_id_returns_none_for_non_existent`
- [x] 3.5 Execute tests: confirm all pass

## 4. Audit Schemas — Implementation

- [x] 4.1 Implement `backend/app/schemas/audit.py` — `AuditLogResponse`, `AuditLogListResponse(items, total, offset, limit)` with `extra='forbid'`
- [x] 4.2 Write `tests/test_audit_schemas.py` — verify serialization, extra fields rejected

## 5. Audit Service — RED → GREEN → TRIANGULATE

- [x] 5.1 RED: Write failing test `test_audit_service.py` — `test_log_creates_entry` with all fields
- [x] 5.2 GREEN: Implement `backend/app/services/audit_service.py` — `AuditService.log()` with D4 signature, uses repository
- [x] 5.3 Execute tests: confirm GREEN
- [x] 5.4 TRIANGULATE: Add `test_log_with_defaults`, `test_log_with_impersonacion`, `test_log_returns_entry_with_id`
- [x] 5.5 Execute tests: confirm all pass

## 6. Audit Router — RED → GREEN → TRIANGULATE

- [x] 6.1 RED: Write failing integration test `test_audit_router.py` — `test_list_audit_logs` GET /api/v1/audit returns paginated results for user with `auditoria:ver`
- [x] 6.2 GREEN: Implement `backend/app/api/v1/routers/audit.py` — list (filterable) and get-by-id endpoints, both guarded by `require_permission("auditoria:ver")`
- [x] 6.3 Register router in `backend/app/main.py`
- [x] 6.4 Execute tests: confirm GREEN
- [x] 6.5 TRIANGULATE: Add `test_list_filter_by_accion`, `test_list_filter_by_date_range`, `test_list_returns_403_without_permission`, `test_list_returns_401_without_auth`, `test_get_by_id_returns_entry`, `test_get_by_id_returns_404`
- [x] 6.6 Execute tests: confirm all pass

## 7. Alembic Migration 004 — Audit Log Table + Append-Only Trigger

- [x] 7.1 Create migration: `004_audit_log.py` — creates audit_log table with indexes
- [x] 7.2 Add trigger function `reject_audit_log_mods()` + BEFORE UPDATE/DELETE triggers
- [x] 7.3 Add idempotent seed for `auditoria:ver` permission (ensure it exists)
- [x] 7.4 Verify migration rolls forward and backward cleanly
- [x] 7.5 Update `alembic/env.py` — register AuditLog model for autogenerate

## 8. Append-Only DB Trigger Tests

- [x] 8.1 Write `test_audit_log_trigger.py` — `test_update_on_audit_log_rejected`, `test_delete_on_audit_log_rejected`, `test_insert_on_audit_log_succeeds`
- [x] 8.2 Execute tests: confirm all pass

## 9. Integration and Verification

- [x] 9.1 Write `test_audit_integration.py` — full flow: create via service, query via API, verify tenant isolation
- [x] 9.2 Execute full test suite: all tests pass

## 10. Documentation and Cleanup

- [x] 10.1 Run linting/type-checking on all new files — ruff: all checks passed
- [x] 10.2 Update CHANGES.md — mark C-05 as `[x]` when archived
