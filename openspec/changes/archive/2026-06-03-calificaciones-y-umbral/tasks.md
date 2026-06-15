## 0. Safety Net — Pre-existing tests baseline

- [x] 0.1 Run existing test suite: capture "{N} tests passing" baseline
- [x] 0.2 If any test FAILS → STOP, report as pre-existing failure to orchestrator

## 1. Calificacion Model — RED → GREEN → TRIANGULATE

- [x] 1.1 RED: Write failing test `tests/test_calificacion_model.py` — `test_create_calificacion_numeric` expects UUID id, materia_id, cohorte_id, entrada_padron_id, actividad, tipo, nota_numerica, notas_textual=None, aprobado (derived), origen, cargado_por, importado_at, timestamps
- [x] 1.2 GREEN: Implement `backend/app/models/calificacion.py` — `Calificacion` ORM extends BaseModelMixin, FKs to Materia, Cohorte, EntradaPadron, Usuario, with tipo, nota_numerica, nota_textual, aprobado, origen, importado_at
- [x] 1.3 Execute tests: confirm GREEN
- [x] 1.4 TRIANGULATE: Add `test_create_calificacion_textual`, `test_default_origen_importado`, `test_fk_materia_enforced`, `test_fk_entrada_padron_enforced`, `test_fk_cohorte_enforced`, `test_soft_delete_calificacion`, `test_tenant_isolation`
- [x] 1.5 Execute tests: confirm all pass

## 2. UmbralMateria Model — RED → GREEN → TRIANGULATE

- [x] 2.1 RED: Write failing test — `test_create_umbral_defaults`
- [x] 2.2 GREEN: Implement `UmbralMateria` in `backend/app/models/calificacion.py`
- [x] 2.3 Execute tests: confirm GREEN
- [x] 2.4 TRIANGULATE: Add `test_create_umbral_custom_values`, `test_fk_materia_enforced`, `test_soft_delete`, `test_tenant_isolation`
- [x] 2.5 Execute tests: confirm all pass
- [x] 2.6 Update `backend/app/models/__init__.py` — export Calificacion, UmbralMateria

## 3. Aprobado Derivation Logic — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test — `test_numeric_aprobado_true`
- [x] 3.2 GREEN: Implement `compute_aprobado()` pure function
- [x] 3.3 Execute tests: confirm GREEN
- [x] 3.4 TRIANGULATE: Add triangulation tests
- [x] 3.5 Execute tests: confirm all pass

## 4. UmbralRepository — RED → GREEN → TRIANGULATE

- [x] 4.1 RED: Write failing test
- [x] 4.2 GREEN: Implement `backend/app/repositories/umbral_repository.py`
- [x] 4.3 Execute tests: confirm GREEN
- [x] 4.4 TRIANGULATE: Add triangulation tests
- [x] 4.5 Execute tests: confirm all pass

## 5. CalificacionRepository — RED → GREEN → TRIANGULATE

- [x] 5.1 RED: Write failing test
- [x] 5.2 GREEN: Implement `backend/app/repositories/calificacion_repository.py`
- [x] 5.3 Execute tests: confirm GREEN
- [x] 5.4 TRIANGULATE: Add triangulation tests
- [x] 5.5 Execute tests: confirm all pass

## 6. Grade File Parser — RED → GREEN → TRIANGULATE

- [ ] 6.1 RED: Write failing test `tests/test_grade_file_parser.py` — `test_parse_detects_numeric_and_textual`
- [ ] 6.2 GREEN: Implement grade file parser in `services/grade_file_parser.py`
- [ ] 6.3 Execute tests: confirm GREEN
- [ ] 6.4 TRIANGULATE: Add triangulation tests
- [ ] 6.5 Execute tests: confirm all pass

## 7. UmbralService — RED → GREEN → TRIANGULATE

- [x] 7.1 RED: Write failing test
- [x] 7.2 GREEN: Implement `backend/app/services/umbral_service.py`
- [x] 7.3 Execute tests: confirm GREEN
- [x] 7.4 TRIANGULATE: Add triangulation tests
- [x] 7.5 Execute tests: confirm all pass

## 8. CalificacionService (Import) — RED → GREEN → TRIANGULATE

- [x] 8.1 RED: Write failing test
- [x] 8.2 GREEN: Implement `backend/app/services/calificacion_service.py`
- [x] 8.3 Execute tests: confirm GREEN
- [x] 8.4 TRIANGULATE: Add triangulation tests
- [x] 8.5 Execute tests: confirm all pass

## 9. CalificacionService (Reporte Finalización) — RED → GREEN → TRIANGULATE

- [x] 9.1 RED: Write failing test
- [x] 9.2 GREEN: Implement reporte_finalizacion()
- [x] 9.3 Execute tests: confirm GREEN
- [x] 9.4 TRIANGULATE: Add triangulation tests
- [x] 9.5 Execute tests: confirm all pass

## 10. Pydantic Schemas — Implementation

- [ ] 10.1 Implement `backend/app/schemas/calificacion.py` — `CalificacionResponse`, `UmbralResponse`, `UmbralUpdateRequest`, `ActividadDetectada`, `ImportPreviewResponse`, `ImportConfirmRequest`, `ImportConfirmResponse`, `ReporteAlumno`, `ReporteActividadSinCorregir`, `ReporteFinalizacionResponse`. All with `model_config = ConfigDict(extra='forbid', from_attributes=True)` where applicable
- [ ] 10.2 Write `tests/test_calificacion_schemas.py` — verify serialization, extra fields rejected, default values, validation (umbral_pct range)

## 11. Calificaciones Router (Preview + Confirmar) — RED → GREEN → TRIANGULATE

- [ ] 11.1 RED: Write failing integration test `tests/test_calificaciones_router.py` — `test_preview_import_200` POST /api/calificaciones/importar/preview returns ImportPreviewResponse for user with `calificaciones:cargar`
- [ ] 11.2 GREEN: Implement `backend/app/api/v1/routers/calificaciones.py` — `calificaciones_router` with POST /importar/preview (file upload → CalificacionService.preview), guarded by `Depends(require_permission("calificaciones:cargar"))`
- [ ] 11.3 Register router in `backend/app/main.py` under calificaciones_router
- [ ] 11.4 Execute tests: confirm GREEN
- [ ] 11.5 TRIANGULATE: Add `test_confirm_import_201`, `test_403_without_calificaciones_cargar`, `test_401_without_auth`, `test_preview_unsupported_format_400`
- [ ] 11.6 Execute tests: confirm all pass

## 12. Calificaciones Router (Reporte Finalización) — RED → GREEN → TRIANGULATE

- [ ] 12.1 RED: Write failing integration test `tests/test_calificaciones_router.py` — `test_reporte_finalizacion_200` POST /api/calificaciones/importar/reporte-finalizacion returns ReporteFinalizacionResponse for user with `calificaciones:cargar`
- [ ] 12.2 GREEN: Add endpoint to calificaciones_router — POST /importar/reporte-finalizacion, guarded by `calificaciones:cargar`
- [ ] 12.3 Execute tests: confirm GREEN
- [ ] 12.4 TRIANGULATE: Add `test_403_without_permission`, `test_reporte_with_no_pending`
- [ ] 12.5 Execute tests: confirm all pass

## 13. Calificaciones Router (Umbral) — RED → GREEN → TRIANGULATE

- [ ] 13.1 RED: Write failing integration test `tests/test_calificaciones_router.py` — `test_get_umbral_200` GET /api/calificaciones/umbral?materia_id=X returns UmbralResponse for user with `calificaciones:ver`
- [ ] 13.2 GREEN: Add endpoints to calificaciones_router — GET /umbral (query param materia_id, returns default if no config), PUT /umbral (set/update), guarded by `calificaciones:ver` (GET) and `calificaciones:cargar` (PUT)
- [ ] 13.3 Execute tests: confirm GREEN
- [ ] 13.4 TRIANGULATE: Add `test_get_umbral_returns_defaults`, `test_put_umbral_200`, `test_put_umbral_invalid_range_422`, `test_get_umbral_403_without_calificaciones_ver`, `test_put_umbral_403_without_calificaciones_cargar`
- [ ] 13.5 Execute tests: confirm all pass

## 14. Seed Permissions — CALIFICACIONES_CARGAR and CALIFICACIONES_VER

- [ ] 14.1 Verify `calificaciones:cargar` and `calificaciones:ver` exist in the permiso catalog. If not, create them via a data migration or seed script
- [ ] 14.2 Verify tests for the new permissions pass

## 15. Alembic Migration 008 — Calificacion + UmbralMateria

- [ ] 15.1 Generate migration: `008_calificaciones_y_umbral.py` — creates calificacion and umbral_materia tables with all columns, FKs, indexes (IX on materia_id+cohorte_id, IX on entrada_padron_id, IX on cargado_por, UNIQUE partial on umbral_materia)
- [ ] 15.2 Verify migration rolls forward and backward cleanly
- [ ] 15.3 Update `alembic/env.py` — register Calificacion, UmbralMateria models for autogenerate

## 16. Integration and Verification

- [ ] 16.1 Write `test_calificaciones_integration.py` — full E2E: set umbral → preview import → confirm import → verify calificaciones with derived aprobado → reporte-finalizacion → verify pending detection
- [ ] 16.2 Execute full test suite: all tests pass
- [ ] 16.3 Run linting/type-checking on all new and modified files
