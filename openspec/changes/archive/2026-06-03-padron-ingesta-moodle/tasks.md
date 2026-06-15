## 0. Safety Net — Pre-existing tests baseline

- [x] 0.1 Run existing test suite: capture "{N} tests passing" baseline
- [x] 0.2 If any test FAILS → STOP, report as pre-existing failure to orchestrator

## 1. VersionPadron Model — RED → GREEN → TRIANGULATE

- [x] 1.1 RED: Write failing test `tests/test_version_padron_model.py` — `test_create_version_padron` expects UUID id, tenant_id, materia_id, cohorte_id, cargado_por, cargado_at, activa=True, timestamps
- [x] 1.2 GREEN: Implement `backend/app/models/padron.py` — `VersionPadron` ORM extends BaseModelMixin, FKs to Materia, Cohorte, Usuario, partial unique index on (tenant_id, materia_id, cohorte_id) WHERE activa AND deleted_at IS NULL
- [x] 1.3 Execute tests: confirm GREEN
- [x] 1.4 TRIANGULATE: Add `test_unique_active_version_constraint`, `test_multiple_inactive_versions_allowed`, `test_version_fk_materia_enforced`, `test_version_fk_cohorte_enforced`, `test_version_soft_delete_does_not_block_new_active`, `test_tenant_isolation`
- [x] 1.5 Execute tests: confirm all pass
- [x] 1.6 Update `backend/app/models/__init__.py` — export VersionPadron

## 2. EntradaPadron Model — RED → GREEN → TRIANGULATE

- [x] 2.1 RED: Write failing test `tests/test_entrada_padron_model.py` — `test_create_entrada_padron` expects UUID id, version_id, tenant_id, nombre, apellidos, email (encrypted), comision, regional, timestamps
- [x] 2.2 GREEN: Implement `EntradaPadron` in `backend/app/models/padron.py` — extends BaseModelMixin, FK to VersionPadron, FK to Usuario (nullable), EncryptedString for email, denormalized nombre/apellidos
- [x] 2.3 Execute tests: confirm GREEN
- [x] 2.4 TRIANGULATE: Add `test_nullable_usuario_id`, `test_fk_usuario_enforced_when_not_null`, `test_fk_version_enforced`, `test_email_encrypted_in_db`, `test_email_decrypted_on_orm_read`, `test_multiple_entries_per_version`, `test_soft_delete_entry`, `test_list_excludes_soft_deleted`, `test_tenant_isolation`
- [x] 2.5 Execute tests: confirm all pass
- [x] 2.6 Update `backend/app/models/__init__.py` — export EntradaPadron

## 3. PadronRepository — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test `tests/test_padron_repository.py` — `test_create_version` persists and returns VersionPadron with id
- [x] 3.2 GREEN: Implement `backend/app/repositories/padron_repository.py` — `PadronRepository` with create_version, get_active_version, deactivate_previous_active, create_entries, get_entries, vaciar_entries, list_versions, get_version
- [x] 3.3 Execute tests: confirm GREEN
- [x] 3.4 TRIANGULATE: Add `test_get_active_version_found`, `test_get_active_version_none`, `test_deactivate_previous_active_updates_count`, `test_create_entries_bulk_create`, `test_get_entries_paginated`, `test_get_entries_total_count`, `test_vaciar_entries_soft_deletes`, `test_vaciar_entries_returns_count`, `test_list_versions_paginated`, `test_tenant_isolation_on_all_methods`
- [x] 3.5 Execute tests: confirm all pass

## 4. File Parser — RED → GREEN → TRIANGULATE

- [x] 4.1 RED: Write failing test `tests/test_file_parser.py` — `test_parse_xlsx` parses valid .xlsx returning ParseResult with total_rows and rows
- [x] 4.2 GREEN: Implement `backend/app/services/file_parser.py` — `FileParser` with `parse()` and `parse_bytes()` supporting .xlsx (openpyxl) and .csv (csv module), auto-column detection, errors collection
- [x] 4.3 Execute tests: confirm GREEN
- [x] 4.4 TRIANGULATE: Add `test_parse_csv`, `test_parse_missing_optional_columns`, `test_parse_alternate_headers`, `test_parse_unsupported_format_raises`, `test_parse_empty_file`, `test_parse_skips_rows_with_missing_required`, `test_parse_normalizes_header_names`, `test_detect_column_mapping_all_standard`, `test_detect_column_mapping_partial`
- [x] 4.5 Execute tests: confirm all pass

## 5. Moodle WS Client — RED → GREEN → TRIANGULATE

- [x] 5.1 RED: Write failing test `tests/test_moodle_ws.py` — `test_get_enrolled_users_returns_students` expects list of MoodleStudent dataclass with nombre, apellidos, email
- [x] 5.2 GREEN: Implement `backend/app/integrations/moodle_ws.py` — `MoodleWSClient` with `get_enrolled_users()` using httpx async HTTP, `MoodleStudent` dataclass, `MoodleConnectionError` and `MoodleAuthError` exceptions, `MoodleWSClientProtocol` Protocol class
- [x] 5.3 Execute tests: confirm GREEN
- [x] 5.4 TRIANGULATE: Add `test_moodle_connection_error`, `test_moodle_auth_error`, `test_moodle_timeout`, `test_protocol_accepts_mock`, `test_moodle_unavailable_fallback_indicator`
- [x] 5.5 Execute tests: confirm all pass

## 6. PadronService (Import + Vaciar) — RED → GREEN → TRIANGULATE

- [x] 6.1 RED: Write failing test `tests/test_padron_service.py` — `test_preview_returns_parse_result` expects ImportPreviewResponse from preview()
- [x] 6.2 GREEN: Implement `backend/app/services/padron_service.py` — `PadronService` with preview() (parse + return), confirm_import() (create version + deactivate previous + create entries + audit), vaciar_version() (soft-delete entries + audit)
- [x] 6.3 Execute tests: confirm GREEN
- [x] 6.4 TRIANGULATE: Add `test_confirm_import_creates_version`, `test_confirm_import_deactivates_previous`, `test_confirm_import_creates_entries`, `test_confirm_import_calls_audit`, `test_confirm_import_with_column_override`, `test_confirm_import_empty_file_raises`, `test_vaciar_non_active_version_succeeds`, `test_vaciar_active_version_raises_409`, `test_vaciar_nonexistent_version_raises_404`, `test_vaciar_calls_audit`
- [x] 6.5 Execute tests: confirm all pass

## 7. Pydantic Schemas — Implementation

- [x] 7.1 Implement `backend/app/schemas/padron.py` — `VersionPadronResponse`, `EntradaPadronResponse`, `ImportPreviewResponse`, `ImportConfirmRequest`, `VaciarResponse`, `VersionListResponse`, `EntradaListResponse`. All with `model_config = ConfigDict(extra='forbid', from_attributes=True)` where applicable
- [x] 7.2 Write `tests/test_padron_schemas.py` — verify serialization, extra fields rejected, ImportPreviewResponse structure

## 8. Padron Router (Preview + Confirmar) — RED → GREEN → TRIANGULATE

- [x] 8.1 RED: Write failing integration test `tests/test_padron_router.py` — `test_preview_import_200` POST /api/v1/padron/importar/preview returns ImportPreviewResponse for user with `padron:cargar`
- [x] 8.2 GREEN: Implement `backend/app/api/v1/routers/padron.py` — `padron_router` with preview (POST file upload → FileParser), guarded by `Depends(require_permission("padron:cargar"))`
- [x] 8.3 Register router in `backend/app/main.py` under `/api/v1/padron`
- [x] 8.4 Execute tests: confirm GREEN
- [x] 8.5 TRIANGULATE: Add `test_confirm_import_201`, `test_403_without_padron_cargar`, `test_401_without_auth`, `test_preview_unsupported_format_400`
- [x] 8.6 Execute tests: confirm all pass

## 9. Padron Router (Versiones + Entradas) — RED → GREEN → TRIANGULATE

- [x] 9.1 RED: Write failing integration test `tests/test_padron_router.py` — `test_list_versiones_200` GET /api/v1/padron/versiones returns paginated VersionPadronResponse for user with `padron:ver`
- [x] 9.2 GREEN: Add endpoints to `padron_router` — GET /versiones (list, filter by materia_id, cohorte_id), GET /versiones/{id} (detail), GET /versiones/{id}/entradas (paginated entries), guarded by `Depends(require_permission("padron:ver"))`
- [x] 9.3 Execute tests: confirm GREEN
- [x] 9.4 TRIANGULATE: Add `test_get_version_detail_200`, `test_get_version_404`, `test_list_entradas_200`, `test_list_entradas_empty`, `test_filter_versiones_by_materia`, `test_filter_versiones_by_cohorte`, `test_403_without_padron_ver`
- [x] 9.5 Execute tests: confirm all pass

## 10. Padron Router (Vaciar) — RED → GREEN → TRIANGULATE

- [x] 10.1 RED: Write failing integration test `tests/test_padron_router.py` — `test_vaciar_non_active_version_200` POST /api/v1/padron/versiones/{id}/vaciar
- [x] 10.2 GREEN: Add endpoint to `padron_router` — POST /versiones/{id}/vaciar, guarded by `padron:cargar`
- [x] 10.3 Execute tests: confirm GREEN
- [x] 10.4 TRIANGULATE: Add `test_vaciar_active_version_409`, `test_vaciar_nonexistent_404`
- [x] 10.5 Execute tests: confirm all pass

## 11. Alembic Migration 007 — VersionPadron + EntradaPadron

- [x] 11.1 Verify migration: `007_padron_ingesta_moodle.py` — creates version_padron and entrada_padron tables. Fixed missing `cargado_at` column, added FK constraints for materia_id, cohorte_id, cargado_por, and usuario_id. Aligned column types with model definitions (String vs Text).
- [x] 11.2 Verify migration rolls forward and backward cleanly
- [x] 11.3 Update `alembic/env.py` — register VersionPadron, EntradaPadron models for autogenerate

## 12. Integration and Verification

- [x] 12.1 Write `test_padron_integration.py` — full E2E: preview → confirm → list versiones → get detail → list entradas → deactivate → vaciar → verify soft-delete in DB
- [x] 12.2 Execute full test suite: all tests pass
- [x] 12.3 Run linting/type-checking on all new and modified files — ruff: all checks passed
