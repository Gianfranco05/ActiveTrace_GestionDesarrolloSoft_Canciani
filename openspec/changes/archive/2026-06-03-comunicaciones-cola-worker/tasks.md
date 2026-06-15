## 0. Safety Net — Pre-existing tests baseline

- [x] 0.1 Run existing test suite from `backend/`: capture "580 passed, 2 skipped" baseline
- [x] 0.2 If any test FAILS → STOP, report as pre-existing failure to orchestrator

## 1. Tenant Config + Seed Permissions + Audit Codes

- [x] 1.1 Add `requiere_aprobacion_comunicaciones` boolean column to Tenant model (default false)
- [x] 1.2 Create Alembic migration for tenant column addition
- [x] 1.3 Seed permissions in permiso catalog: `comunicacion:enviar` (PROFESOR propio, COORDINADOR, ADMIN), `comunicacion:aprobar` (COORDINADOR, ADMIN), `comunicacion:ver` (PROFESOR propio, TUTOR propio, COORDINADOR, ADMIN)
- [x] 1.4 Add audit action codes: `COMUNICACION_PREVIEW`, `COMUNICACION_ENVIAR`, `COMUNICACION_APROBAR`, `COMUNICACION_CANCELAR`
- [x] 1.5 Write tests: permission seeding, audit code registration

## 2. Comunicacion ORM Model + Alembic Migration

- [x] 2.1 Implement `backend/app/models/comunicacion.py` — Comunicacion ORM model with soft-delete mixin, tenant_id, lote_id, estado enum, encrypted destinatario, template fields, approval fields
- [x] 2.2 Implement `EstadoComunicacion` enum: PENDIENTE, ENVIANDO, ENVIADO, ERROR, CANCELADO
- [x] 2.3 Create Alembic migration `Migración 0NN: comunicacion` — create comunicacion table with indexes on (tenant_id, estado), (lote_id), (tenant_id, created_at)
- [x] 2.4 Write tests: model fields, enum values, soft-delete mixin, tenant isolation at model level

## 3. ComunicacionRepository + Encrypted Destinatario

- [x] 3.1 RED: Write failing test `tests/test_comunicacion_repository.py` — test_create_comunicacion encrypts destinatario
- [x] 3.2 GREEN: Implement `backend/app/repositories/comunicacion_repository.py` — CRUD with encrypted write (AES-256, reuse C-07 encryption service), decrypted read
- [x] 3.3 Execute tests: confirm GREEN
- [x] 3.4 TRIANGULATE: Add tests for list_by_estado, list_by_lote, list_by_date_range, get_by_id, soft_delete, tenant scope enforced, cross-tenant isolation, encrypted storage round-trip
- [x] 3.5 Execute tests: confirm all pass

## 4. State Machine — RED → GREEN → TRIANGULATE

- [x] 4.1 RED: Write failing test `tests/test_comunicacion_service.py` — test_valid_transition_pendiente_to_enviando
- [x] 4.2 GREEN: Implement `EstadoComunicacion` + `ALLOWED_TRANSITIONS` dict + `InvalidStateTransitionError` in `backend/app/services/comunicacion_service.py`
- [x] 4.3 Execute tests: confirm GREEN
- [x] 4.4 TRIANGULATE: Add tests for all valid transitions (Pendiente→Enviando, Pendiente→Cancelado, Enviando→Enviado, Enviando→Error), all invalid transitions (Enviado→any, Error→any, Cancelado→any, Enviando→Cancelado), terminal state immutability
- [x] 4.5 Execute tests: confirm all pass

## 5. Preview Service — RED → GREEN → TRIANGULATE

- [x] 5.1 RED: Write failing test `tests/test_comunicacion_service.py` — test_preview_returns_sample_recipients
- [x] 5.2 GREEN: Implement `ComunicacionService.preview()` — load recipients from EntradaPadron, render template for sample (first 5), generate preview_token (hash + timestamp), return sample + total_estimado + preview_token
- [x] 5.3 Execute tests: confirm GREEN
- [x] 5.4 TRIANGULATE: Add tests for preview renders template variables, preview_with_invalid_template_id_404, preview_logs_audit, preview_token_format, preview_token_expiration
- [x] 5.5 Execute tests: confirm all pass

## 6. Enqueue Service — RED → GREEN → TRIANGULATE

- [x] 6.1 RED: Write failing test `tests/test_comunicacion_service.py` — test_enqueue_creates_comunicacion_records
- [x] 6.2 GREEN: Implement `ComunicacionService.enqueue()` — validate preview_token, generate lote_id, create one Comunicacion per recipient in Pendiente, return lote_id + count
- [x] 6.3 Execute tests: confirm GREEN
- [x] 6.4 TRIANGULATE: Add tests for enqueue_without_preview_token_400, enqueue_expired_preview_token_400, enqueue_different_lote_id_per_call, enqueue_requires_aprobacion_denormalized, enqueue_logs_audit
- [x] 6.5 Execute tests: confirm all pass

## 7. Approve Service — RED → GREEN → TRIANGULATE

- [x] 7.1 RED: Write failing test `tests/test_comunicacion_service.py` — test_approve_by_lote
- [x] 7.2 GREEN: Implement `ComunicacionService.approve()` — update aprobado_por for all Pendiente records in lote OR single id, skip already-approved, return count
- [x] 7.3 Execute tests: confirm GREEN
- [x] 7.4 TRIANGULATE: Add tests for approve_by_individual_id, approve_already_approved_skipped, approve_non_existent_lote_404, approve_logs_audit, approve_without_permission_403
- [x] 7.5 Execute tests: confirm all pass

## 8. Cancel Service — RED → GREEN → TRIANGULATE

- [x] 8.1 RED: Write failing test `tests/test_comunicacion_service.py` — test_cancel_by_lote
- [x] 8.2 GREEN: Implement `ComunicacionService.cancel()` — transition Pendiente→Cancelado for all records in lote OR single id, skip non-Pendiente, return count
- [x] 8.3 Execute tests: confirm GREEN
- [x] 8.4 TRIANGULATE: Add tests for cancel_by_individual_id, cancel_ignores_enviando_records, cancel_ignores_terminal_records, cancel_non_existent_lote_404, cancel_logs_audit
- [x] 8.5 Execute tests: confirm all pass

## 9. Pydantic Schemas

- [x] 9.1 Implement `backend/app/schemas/comunicacion.py` — all request/response DTOs: `ComunicacionResponse`, `ComunicacionListResponse`, `PreviewRequest`, `PreviewResponse`, `EnqueueRequest`, `EnqueueResponse`, `ApproveResponse`, `CancelResponse`, `ComunicacionFilterParams`. All with `model_config = ConfigDict(extra='forbid', from_attributes=True)`
- [x] 9.2 Write tests: serialization, extra fields rejected, default values, filter params validation

## 10. Template Engine — RED → GREEN → TRIANGULATE

- [x] 10.1 RED: Write failing test `tests/test_comunicacion_service.py` — test_template_render_substitutes_variables
- [x] 10.2 GREEN: Implement `TemplateEngine` — resolve `{{nombre}}`, `{{apellidos}}`, `{{materia}}`, `{{comision}}`, `{{fecha}}` from Pydantic TemplateVariables; use str.replace loop
- [x] 10.3 Execute tests: confirm GREEN
- [x] 10.4 TRIANGULATE: Add tests for all defined variables, unknown variables left as-is, empty variables handled gracefully, template without variables returns unchanged
- [x] 10.5 Execute tests: confirm all pass

## 11. Worker Implementation — RED → GREEN → TRIANGULATE

- [x] 11.1 RED: Write failing test `tests/test_comunicacion_worker.py` — test_worker_polls_pendiente_records
- [x] 11.2 GREEN: Implement `backend/app/workers/comunicacion_worker.py` — poll loop with FOR UPDATE SKIP LOCKED, BATCH_SIZE and POLL_INTERVAL config, startup recovery for stuck Enviando, graceful shutdown
- [x] 11.3 Implement `EmailSender` protocol/mock — injectable interface, mock always succeeds (configurable failure rate for testing)
- [x] 11.4 Execute tests: confirm GREEN
- [x] 11.5 TRIANGULATE: Add tests for worker_transitions_enviando, worker_transitions_enviado, worker_transitions_error, worker_skips_requiere_aprobacion_without_approved, worker_startup_recovers_stuck_enviando, worker_batch_size_respected, worker_graceful_shutdown
- [x] 11.6 Execute tests: confirm all pass

## 12. Router Implementation — RED → GREEN → TRIANGULATE

- [ ] 12.1 RED: Write failing integration test `tests/test_comunicaciones_router.py` — test_preview_200
- [ ] 12.2 GREEN: Implement `backend/app/api/v1/routers/comunicaciones.py` — 6 endpoints:
  - `POST /api/comunicaciones/preview` → `comunicacion:enviar`
  - `POST /api/comunicaciones/enviar` → `comunicacion:enviar`
  - `POST /api/comunicaciones/{id}/aprobar` → `comunicacion:aprobar`
  - `POST /api/comunicaciones/{id}/cancelar` → `comunicacion:enviar`
  - `GET /api/comunicaciones` → `comunicacion:ver`
  - `GET /api/comunicaciones/{id}` → `comunicacion:ver`
- [ ] 12.3 Register router in `backend/app/main.py` under `/api/comunicaciones`
- [ ] 12.4 Execute tests: confirm GREEN
- [ ] 12.5 TRIANGULATE: Add tests for all 6 endpoints 200, 401 without auth, 403 without permission (all 3 permissions), 404 for non-existent lote/id, filter params on list endpoint, scope isolation PROFESOR vs COORDINADOR
- [ ] 12.6 Execute tests: confirm all pass

## 13. Full Integration Test

- [ ] 13.1 Write `test_comunicaciones_integration.py` — full E2E: seed data → preview → enqueue → verify Pendiente count → worker poll → verify Enviado count → approve (for approval-required tenant) → verify worker processes approved → cancel → verify Cancelado
- [ ] 13.2 Execute full test suite: verify baseline (580 passed, 2 skipped) + new tests all green
- [ ] 13.3 Run linting/type-checking on all new and modified files