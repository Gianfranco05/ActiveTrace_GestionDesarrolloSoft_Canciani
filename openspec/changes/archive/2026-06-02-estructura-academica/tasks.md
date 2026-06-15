## 1. EstadoRegistro Enum — Implementation

- [x] 1.1 Implement `backend/app/core/estado_registro.py` — `EstadoRegistro(str, Enum)` with `ACTIVA = "Activa"`, `INACTIVA = "Inactiva"`
- [x] 1.2 Write `tests/test_estado_registro.py` — verify members, iteration, inversion via `value` and `name`

## 2. Carrera Model — RED → GREEN → TRIANGULATE

- [x] 2.1 RED: Write failing test `test_carrera_model.py` — `test_create_carrera` expects UUID id, tenant_id, codigo, nombre, estado, timestamps
- [x] 2.2 GREEN: Implement `backend/app/models/carrera.py` — Carrera ORM extends BaseModelMixin, UNIQUE(tenant_id, codigo) with partial index WHERE deleted_at IS NULL, estado defaults to "Activa"
- [x] 2.3 Execute tests: confirm GREEN
- [x] 2.4 TRIANGULATE: Add `test_carrera_codigo_unique_per_tenant`, `test_carrera_same_codigo_different_tenant`, `test_carrera_default_estado`, `test_carrera_soft_delete`
- [x] 2.5 Execute tests: confirm all pass
- [x] 2.6 Update `backend/app/models/__init__.py` — export Carrera

## 3. CarreraRepository — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test `test_carrera_repository.py` — `test_create_carrera` persists and returns entity with id
- [x] 3.2 GREEN: Implement `backend/app/repositories/carrera_repository.py` — `CarreraRepository(BaseRepository[Carrera])` with `get_by_codigo(codigo) -> Carrera | None`
- [x] 3.3 Execute tests: confirm GREEN
- [x] 3.4 TRIANGULATE: Add `test_get_by_codigo_found`, `test_get_by_codigo_not_found`, `test_list_excludes_soft_deleted`, `test_tenant_isolation`
- [x] 3.5 Execute tests: confirm all pass

## 4. Cohorte Model — RED → GREEN → TRIANGULATE

- [x] 4.1 RED: Write failing test `test_cohorte_model.py` — `test_create_cohorte` expects UUID id, tenant_id, carrera_id, nombre, anio, vig_desde, vig_hasta=None, timestamps
- [x] 4.2 GREEN: Implement `backend/app/models/cohorte.py` — Cohorte ORM extends BaseModelMixin, FK to Carrera ON DELETE RESTRICT, UNIQUE(tenant_id, carrera_id, nombre) with partial index
- [x] 4.3 Execute tests: confirm GREEN
- [x] 4.4 TRIANGULATE: Add `test_cohorte_nombre_unique_per_carrera`, `test_cohorte_default_estado`, `test_cohorte_vig_hasta_nullable`, `test_cohorte_fk_carrera_enforced`, `test_cohorte_soft_delete`
- [x] 4.5 Execute tests: confirm all pass
- [x] 4.6 Update `backend/app/models/__init__.py` — export Cohorte

## 5. CohorteRepository — RED → GREEN → TRIANGULATE

- [x] 5.1 RED: Write failing test `test_cohorte_repository.py` — `test_create_cohorte` persists and returns entity with id
- [x] 5.2 GREEN: Implement `backend/app/repositories/cohorte_repository.py` — `CohorteRepository(BaseRepository[Cohorte])` with `get_by_carrera(carrera_id)`, `get_activas_by_carrera(carrera_id)`
- [x] 5.3 Execute tests: confirm GREEN
- [x] 5.4 TRIANGULATE: Add `test_get_by_carrera_returns_cohortes`, `test_get_by_carrera_empty`, `test_get_activas_by_carrera`, `test_tenant_isolation`
- [x] 5.5 Execute tests: confirm all pass

## 6. Cohorte Service — RED → GREEN → TRIANGULATE (business rule: carrera must be active)

- [x] 6.1 RED: Write failing test `test_cohorte_service.py` — `test_create_cohorte_with_active_carrera_succeeds`
- [x] 6.2 GREEN: Implement `backend/app/services/estructura_service.py` — `CohorteService.create()` that checks `carrera.estado == ACTIVA` before delegating to repository
- [x] 6.3 Execute tests: confirm GREEN
- [x] 6.4 TRIANGULATE: Add `test_create_cohorte_with_inactive_carrera_raises_error`, `test_update_cohorte_to_activa_with_inactive_carrera_raises_error`
- [x] 6.5 Execute tests: confirm all pass

## 7. Materia Model — RED → GREEN → TRIANGULATE

- [x] 7.1 RED: Write failing test `test_materia_model.py` — `test_create_materia` expects UUID id, tenant_id, codigo, nombre, timestamps
- [x] 7.2 GREEN: Implement `backend/app/models/materia.py` — Materia ORM extends BaseModelMixin, UNIQUE(tenant_id, codigo) with partial index, estado defaults to "Activa"
- [x] 7.3 Execute tests: confirm GREEN
- [x] 7.4 TRIANGULATE: Add `test_materia_codigo_unique_per_tenant`, `test_materia_same_codigo_different_tenant`, `test_materia_default_estado`, `test_materia_soft_delete`, `test_materia_no_carrera_relation` (catalog-only per ADR-006)
- [x] 7.5 Execute tests: confirm all pass
- [x] 7.6 Update `backend/app/models/__init__.py` — export Materia

## 8. MateriaRepository — RED → GREEN → TRIANGULATE

- [x] 8.1 RED: Write failing test `test_materia_repository.py` — `test_create_materia` persists and returns entity with id
- [x] 8.2 GREEN: Implement `backend/app/repositories/materia_repository.py` — `MateriaRepository(BaseRepository[Materia])` with `get_by_codigo(codigo) -> Materia | None`
- [x] 8.3 Execute tests: confirm GREEN
- [x] 8.4 TRIANGULATE: Add `test_get_by_codigo_found`, `test_get_by_codigo_not_found`, `test_list_excludes_soft_deleted`, `test_tenant_isolation`
- [x] 8.5 Execute tests: confirm all pass

## 9. Schemas — Implementation

- [x] 9.1 Implement `backend/app/schemas/estructura.py` — `CarreraCreate`, `CarreraUpdate`, `CarreraResponse`, `CohorteCreate`, `CohorteUpdate`, `CohorteResponse`, `MateriaCreate`, `MateriaUpdate`, `MateriaResponse`, plus `EstructuraListResponse(items, total, offset, limit)`. All with `model_config = ConfigDict(extra='forbid', from_attributes=True)`
- [x] 9.2 Write `tests/test_estructura_schemas.py` — verify serialization, extra fields rejected

## 10. Carrera Router — RED → GREEN → TRIANGULATE

- [x] 10.1 RED: Write failing integration test `test_estructura_router.py` — `test_list_carreras` GET /api/v1/estructura/carreras returns paginated results for user with `estructura:gestionar`
- [x] 10.2 GREEN: Implement `backend/app/api/v1/routers/estructura.py` — `carreras_router` with CRUD, guarded by `Depends(require_permission("estructura:gestionar"))`
- [x] 10.3 Register router in `backend/app/main.py` under `/api/v1/estructura`
- [x] 10.4 Execute tests: confirm GREEN
- [x] 10.5 TRIANGULATE: Add `test_create_carrera`, `test_create_duplicate_codigo_409`, `test_get_carrera_by_id`, `test_update_carrera`, `test_soft_delete_carrera`, `test_carrera_returns_403_without_permission`, `test_carrera_returns_401_without_auth`
- [x] 10.6 Execute tests: confirm all pass

## 11. Cohorte Router — RED → GREEN → TRIANGULATE

- [x] 11.1 RED: Write failing integration test — `test_list_cohortes` GET /api/v1/estructura/cohortes returns paginated results
- [x] 11.2 GREEN: Implement `cohortes_router` in `estructura.py` with CRUD, uses CohorteService for business rule
- [x] 11.3 Execute tests: confirm GREEN
- [x] 11.4 TRIANGULATE: Add `test_create_cohorte`, `test_create_cohorte_inactive_carrera_409`, `test_list_cohortes_filter_by_carrera`, `test_update_cohorte`, `test_soft_delete_cohorte`, `test_cohorte_403_without_permission`
- [x] 11.5 Execute tests: confirm all pass

## 12. Materia Router — RED → GREEN → TRIANGULATE

- [x] 12.1 RED: Write failing integration test — `test_list_materias` GET /api/v1/estructura/materias returns paginated results
- [x] 12.2 GREEN: Implement `materias_router` in `estructura.py` with CRUD, guarded by `estructura:gestionar`
- [x] 12.3 Execute tests: confirm GREEN
- [x] 12.4 TRIANGULATE: Add `test_create_materia`, `test_create_duplicate_codigo_409`, `test_get_materia_by_id`, `test_update_materia`, `test_soft_delete_materia`, `test_materia_403_without_permission`
- [x] 12.5 Execute tests: confirm all pass

## 13. Alembic Migration 005 — Estructura Académica Tables

- [x] 13.1 Create migration: `005_estructura_academica.py` — creates carrera, cohorte, materia tables with indexes and FKs per D10
- [x] 13.2 Verify migration rolls forward and backward cleanly
- [x] 13.3 Update `alembic/env.py` — register Carrera, Cohorte, Materia models for autogenerate

## 14. Integration and Verification

- [x] 14.1 Write `test_estructura_integration.py` — full flow: create carrera → create cohorte → create materia → verify all accessible via API with tenant isolation
- [x] 14.2 Execute full test suite: all tests pass
- [x] 14.3 Run linting/type-checking on all new files — ruff: all checks passed
