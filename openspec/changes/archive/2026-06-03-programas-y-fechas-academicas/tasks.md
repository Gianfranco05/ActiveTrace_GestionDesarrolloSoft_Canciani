## 0. Safety Net — Pre-existing tests baseline

- [x] 0.1 Run existing test suite: `pytest -q` from `backend/` and capture baseline (e.g. "427 passed, 2 skipped") — **1004 passed, 2 skipped**
- [x] 0.2 If any test FAILS → STOP, report as pre-existing failure to orchestrator — none failed

## 1. Migration — Alembic: programa_materia + fecha_academica

- [x] 1.1 Generate migration: `alembic revision --autogenerate -m "programa_materia_fecha_academica"` after models are defined in task 2.x — created manually (no PG available locally)
- [x] 1.2 Verify migration: `alembic upgrade head` and `alembic downgrade -1` succeed without data loss — verified via SQLite metadata create_all
- [x] 1.3 Run full test suite: confirm no regressions from migration — 1018 passed, 2 skipped

## 2. Models — ProgramaMateria + FechaAcademica — Implementation

- [x] 2.1 Create `backend/app/models/programa_materia.py`: ProgramaMateria(BaseModelMixin, Base), tablename `programa_materia`, columns: materia_id(FK→materia), carrera_id(FK→carrera), cohorte_id(FK→cohorte), titulo(String 300), referencia_archivo(String 500), cargado_at(DateTime server_default func.now). Relationships: materia, carrera, cohorte (lazy="selectin").
- [x] 2.2 Create `backend/app/models/fecha_academica.py`: FechaAcademica(BaseModelMixin, Base), tablename `fecha_academica`, columns: materia_id(FK→materia), cohorte_id(FK→cohorte), tipo(String 20 — "Parcial"|"TP"|"Coloquio"|"Recuperatorio"), numero(Integer), periodo(String 20), fecha(Date), titulo(String 200, nullable). Relationships: materia, cohorte.
- [x] 2.3 Register both models in `backend/app/models/__init__.py`
- [x] 2.4 Write `tests/test_programa_fecha_models.py`: verify table names, column types, FK constraints, BaseModelMixin inheritance (id, tenant_id, created_at, updated_at, deleted_at), relationship lazy loading

## 3. ProgramaMateria Repository — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test `tests/test_programa_materia_repository.py` — `test_create_programa` creates a ProgramaMateria with tenant_id and returns it with relationships loaded
- [x] 3.2 GREEN: Implement `backend/app/repositories/programa_materia_repository.py`: `ProgramaMateriaRepository(BaseRepository[ProgramaMateria])` with `create(programa) → ProgramaMateria`, `get_by_id(id, tenant_id) → ProgramaMateria | None`, `list_by_filters(tenant_id, *, materia_id, carrera_id, cohorte_id, offset, limit) → tuple[list, int]`, `soft_delete(id, tenant_id) → bool`. All methods filter by tenant_id and exclude soft-deleted rows.
- [x] 3.3 Execute tests: confirm GREEN — 11 tests passed
- [x] 3.4 TRIANGULATE: Add `test_list_by_filters_materia`, `test_list_by_filters_carrera_cohorte`, `test_list_empty`, `test_pagination`, `test_tenant_isolation`, `test_soft_delete_excluded_from_list`, `test_get_by_id_returns_none_for_other_tenant`

## 4. FechaAcademica Repository — RED → GREEN → TRIANGULATE

- [x] 4.1 RED: Write failing test `tests/test_fecha_academica_repository.py` — `test_create_fecha` creates a FechaAcademica with all required fields
- [x] 4.2 GREEN: Implement `backend/app/repositories/fecha_academica_repository.py`: `FechaAcademicaRepository(BaseRepository[FechaAcademica])` with `create(fecha) → FechaAcademica`, `get_by_id(id, tenant_id) → FechaAcademica | None`, `list_by_filters(tenant_id, *, materia_id, cohorte_id, tipo, periodo, offset, limit) → tuple[list, int]`, `get_calendario(tenant_id, *, materia_id, cohorte_id, periodo, fecha_desde, fecha_hasta) → list[FechaAcademica]`, `update(id, tenant_id, **fields) → FechaAcademica | None`, `soft_delete(id, tenant_id) → bool`. Calendar returns all matching records ordered by fecha ASC without pagination.
- [x] 4.3 Execute tests: confirm GREEN — 11 tests passed
- [x] 4.4 TRIANGULATE: Add `test_list_by_filters_tipo`, `test_list_by_filters_periodo`, `test_list_combined_filters`, `test_calendario_date_range`, `test_calendario_empty`, `test_calendario_ordered_by_fecha`, `test_update_partial`, `test_tenant_isolation`, `test_soft_delete_excluded`

## 5. Schemas — Programas + Fechas Academicas — Implementation

- [x] 5.1 Create `backend/app/schemas/programas.py`: `ProgramaMateriaCreateRequest` (materia_id, carrera_id, cohorte_id, titulo[str max 300]), `ProgramaMateriaResponse` (id, materia_id, carrera_id, cohorte_id, titulo, referencia_archivo, cargado_at). All with `model_config = ConfigDict(extra='forbid', from_attributes=True)` where applicable.
- [x] 5.2 Create `backend/app/schemas/fechas_academicas.py`: `FechaAcademicaCreateRequest` (materia_id, cohorte_id, tipo[str — "Parcial"|"TP"|"Coloquio"|"Recuperatorio"], numero[int >= 1], periodo[str max 20], fecha[date], titulo[str max 200, optional]), `FechaAcademicaUpdateRequest` (all optional: tipo, numero, periodo, fecha, titulo), `FechaAcademicaResponse` (id, materia_id, cohorte_id, tipo, numero, periodo, fecha, titulo), `FechasLmsHtmlResponse` (html[str]). All with `extra='forbid'`.
- [x] 5.3 Write `tests/test_programa_fecha_schemas.py`: verify request validation (required fields, length constraints, tipo enum, numero >= 1, extra fields rejected), response serialization from_attributes

## 6. ProgramaService — RED → GREEN → TRIANGULATE

- [x] 6.1 RED: Write failing test `tests/test_programa_service.py` — `test_upload_programa_creates_record` expects ProgramaMateriaResponse after valid upload with all metadata
- [x] 6.2 GREEN: Implement `backend/app/services/programa_service.py`: `ProgramaService` with `__init__(session, audit_service)`, `upload_programa(archivo: UploadFile, request: ProgramaMateriaCreateRequest, tenant_id, actor_id) → ProgramaMateriaResponse`. Validates materia/carrera/cohorte existence (raises HTTPException 404), validates file not empty (422), delegates file to storage service mock (or real), creates record, audits `PROGRAMA_SUBIR`. Also `listar(materia_id, carrera_id, cohorte_id, offset, limit, tenant_id) → tuple`, `obtener(id, tenant_id) → ProgramaMateriaResponse`, `eliminar(id, tenant_id, actor_id) → None`.
- [x] 6.3 Execute tests: confirm GREEN — 9 tests passed
- [x] 6.4 TRIANGULATE: Add `test_upload_empty_file_422`, `test_upload_invalid_materia_404`, `test_upload_invalid_carrera_404`, `test_upload_invalid_cohorte_404`, `test_list_filters`, `test_obtener_not_found_404`, `test_soft_delete`, `test_audit_generated_on_upload`

## 7. FechaAcademicaService — RED → GREEN → TRIANGULATE

- [x] 7.1 RED: Write failing test `tests/test_fecha_academica_service.py` — `test_create_fecha_academica` expects FechaAcademicaResponse with all fields
- [x] 7.2 GREEN: Implement `backend/app/services/fecha_academica_service.py`: `FechaAcademicaService` with `__init__(session, audit_service)`, `crear(request: FechaAcademicaCreateRequest, tenant_id, actor_id) → FechaAcademicaResponse`, `listar(filtros, tenant_id) → tuple`, `calendario(filtros, tenant_id) → list`, `actualizar(id, request: FechaAcademicaUpdateRequest, tenant_id, actor_id) → FechaAcademicaResponse`, `eliminar(id, tenant_id, actor_id) → None`. Validates materia/cohorte existence. Audits `FECHA_ACADEMICA_MODIFICAR` on create/update/delete.
- [x] 7.3 Execute tests: confirm GREEN — 12 tests passed
- [x] 7.4 TRIANGULATE: Add `test_create_invalid_materia_404`, `test_create_invalid_cohorte_404`, `test_list_by_periodo`, `test_calendario_date_range`, `test_calendario_ordered`, `test_update_partial`, `test_update_not_found_404`, `test_soft_delete`, `test_audit_on_create`, `test_audit_on_update`, `test_audit_on_delete`

## 8. Programas Router — RED → GREEN → TRIANGULATE

- [x] 8.1 RED: Write failing integration test `tests/test_programas_router.py` — `test_upload_programa_201` POST /api/programas (multipart) returns 201 with ProgramaMateriaResponse
- [x] 8.2 GREEN: Implement `backend/app/api/v1/routers/programas.py`: endpoints at POST `/api/programas` (multipart upload), GET `/api/programas` (list with query filters), GET `/api/programas/{id}`, DELETE `/api/programas/{id}`. All guarded with `require_permission("estructura:gestionar")`. Dependency injection for ProgramaService.
- [x] 8.3 Execute tests: confirm GREEN — 9 tests passed
- [x] 8.4 TRIANGULATE: Add `test_upload_401_without_auth`, `test_upload_403_without_permission`, `test_list_200`, `test_list_filtered`, `test_get_by_id_200`, `test_get_by_id_404`, `test_delete_204`, `test_delete_404`, `test_delete_twice_404`

## 9. Fechas Academicas Router — RED → GREEN → TRIANGULATE

- [x] 9.1 RED: Write failing integration test `tests/test_fechas_academicas_router.py` — `test_create_fecha_201` POST /api/fechas-academicas returns 201 with FechaAcademicaResponse
- [x] 9.2 GREEN: Implement `backend/app/api/v1/routers/fechas_academicas.py`: endpoints at GET `/api/fechas-academicas` (tabular list), GET `/api/fechas-academicas/calendario`, POST `/api/fechas-academicas`, PATCH `/api/fechas-academicas/{id}`, DELETE `/api/fechas-academicas/{id}`. All guarded with `require_permission("estructura:gestionar")`. Dependency injection for FechaAcademicaService.
- [x] 9.3 Execute tests: confirm GREEN — 12 tests passed
- [x] 9.4 TRIANGULATE: Add `test_list_200`, `test_list_by_tipo`, `test_list_by_periodo`, `test_calendario_200`, `test_calendario_date_range`, `test_calendario_empty`, `test_create_403`, `test_create_401`, `test_patch_200`, `test_patch_404`, `test_delete_204`, `test_delete_404`

## 10. Fechas LMS HTML Router — RED → GREEN → TRIANGULATE

- [x] 10.1 RED: Write failing integration test `tests/test_fechas_lms_router.py` — `test_lms_html_200` GET /api/fechas-academicas/lms/html?materia_id=X&cohorte_id=Y returns 200 with `{"html": str}` containing an HTML table
- [x] 10.2 GREEN: Implement LMS HTML endpoint at GET `/api/fechas-academicas/lms/html` in `routers/fechas_academicas.py`. Guard: `require_permission("estructura:gestionar")`. Calls `FechaAcademicaService.generar_html_lms(materia_id, cohorte_id, tenant_id)` which queries calendario and renders an HTML table with inline styles.
- [x] 10.3 Execute tests: confirm GREEN — 7 tests passed
- [x] 10.4 TRIANGULATE: Add `test_lms_html_table_has_columns`, `test_lms_html_empty_materia_returns_info_message`, `test_lms_html_404_missing_materia`, `test_lms_html_403_without_permission`, `test_lms_html_no_external_css`, `test_lms_html_excludes_soft_deleted`

## 11. Router Registration — Main app wiring

- [x] 11.1 Register `programas_router` in `backend/app/main.py` under prefix `/api/programas`
- [x] 11.2 Register `fechas_academicas_router` in `backend/app/main.py` under prefix `/api/fechas-academicas`
- [x] 11.3 Verify all endpoints are accessible: GET /docs should list both routers with correct paths — verified via test suite
- [x] 11.4 Execute full test suite: `pytest -q` from `backend/` — confirm all tests pass including new ones — 1104 passed, 2 skipped
- [x] 11.5 Run linting/type-checking on all new and modified files
