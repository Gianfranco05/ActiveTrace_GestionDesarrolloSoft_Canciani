## 0. Safety Net — Pre-existing tests baseline

- [x] 0.1 Run existing test suite: capture baseline (e.g. "N tests passing") — 359 passed, 2 skipped
- [x] 0.2 If any test FAILS → STOP, report as pre-existing failure to orchestrator

## 1. Extend AsignacionRepository — Bulk & Equipo operations — RED → GREEN → TRIANGULATE

- [x] 1.1 RED: Write failing test `tests/test_asignacion_repository_equipos.py` — `test_get_equipo_returns_asignaciones` expects all Asignaciones for a (materia_id, carrera_id, cohorte_id) combination
- [x] 1.2 GREEN: Add methods to `backend/app/repositories/asignacion_repository.py` — `get_equipo(materia_id, carrera_id, cohorte_id) -> list[Asignacion]`, `get_equipos_agrupados(tenant_id) -> list[tuple]`, `bulk_create(asignaciones: list[Asignacion]) -> list[Asignacion]`, `update_vigencia_batch(equipo_key, vig_desde, vig_hasta) -> int`, `get_equipo_with_relations(equipo_key) -> list[dict]`, `search_usuarios(query, tenant_id, limit) -> list[Usuario]`
- [x] 1.3 Execute tests: confirm GREEN
- [x] 1.4 TRIANGULATE: Add `test_get_equipo_empty_returns_empty_list`, `test_bulk_create_creates_all`, `test_bulk_create_rollback_on_failure`, `test_update_vigencia_batch_updates_all`, `test_search_usuarios_by_name`, `test_search_usuarios_by_legajo`, `test_tenant_isolation_on_search`
- [x] 1.5 Execute tests: confirm all pass

## 2. New Schemas for Equipos — Implementation

- [x] 2.1 Implement new schemas in `backend/app/schemas/asignaciones.py` — `EquipoResponse`, `EquipoDetailResponse`, `AsignacionMasivaRequest`, `ClonarRequest`, `VigenciaUpdateRequest`, `UsuarioSearchResponse`. All with `model_config = ConfigDict(extra='forbid', from_attributes=True)` where applicable
- [x] 2.2 Write `tests/test_equipo_schemas.py` — verify serialization, extra fields rejected, EquipoResponse includes materia_id/carrera_id/cohorte_id/total_asignaciones, AsignacionMasivaRequest rejects >100 usuario_ids, ClonarRequest validates required fields

## 3. EquipoService — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test `tests/test_equipo_service.py` — `test_listar_mis_equipos_returns_user_asignaciones` expects filtered Asignaciones for authenticated user
- [x] 3.2 GREEN: Implement `backend/app/services/equipo_service.py` — `EquipoService` with methods: `listar_mis_equipos(usuario_id, tenant_id, filtros)`, `listar_equipos(tenant_id)`, `obtener_equipo(materia_id, carrera_id, cohorte_id)`, `asignacion_masiva(request, actor_id)`, `clonar_equipo(request, actor_id)`, `modificar_vigencia(materia_id, carrera_id, cohorte_id, request, actor_id)`, `exportar_equipo(materia_id, carrera_id, cohorte_id)`, `buscar_usuarios(query, tenant_id, limit)`. All methods use audit service for write operations
- [x] 3.3 Execute tests: confirm GREEN
- [x] 3.4 TRIANGULATE: Add `test_listar_equipos_returns_grouped`, `test_asignacion_masiva_creates_all`, `test_asignacion_masiva_rollback_on_missing_usuario`, `test_clonar_equipo_duplicates_assignments`, `test_clonar_equipo_responsable_resolution`, `test_clonar_equipo_only_vigente`, `test_modificar_vigencia_updates_all`, `test_modificar_vigencia_invalid_dates`, `test_exportar_equipo_generates_csv`, `test_buscar_usuarios_returns_matches`, `test_buscar_usuarios_empty`
- [x] 3.5 Execute tests: confirm all pass

## 4. Equipos Router — Mis Equipos (GET) — RED → GREEN → TRIANGULATE

- [x] 4.1 RED: Write failing integration test `tests/test_equipos_router.py` — `test_mis_equipos_returns_own_assignments` GET /api/equipos/mis-equipos returns paginated AsignacionResponse for authenticated user
- [x] 4.2 GREEN: Implement `backend/app/api/v1/routers/equipos.py` — `mis_equipos` endpoint at GET /api/equipos/mis-equipos with `require_authenticated`, filter by session user_id
- [x] 4.3 Execute tests: confirm GREEN
- [x] 4.4 TRIANGULATE: Add `test_mis_equipos_returns_empty_for_no_assignments`, `test_mis_equipos_401_without_auth`
- [x] 4.5 Execute tests: confirm all pass

## 5. Equipos Router — List & Detail (GET) — RED → GREEN → TRIANGULATE

- [x] 5.1 RED: Write failing integration test — `test_list_equipos_returns_grouped` GET /api/equipos returns paginated EquipoResponse for user with equipos:asignar
- [x] 5.2 GREEN: Implement endpoints in `routers/equipos.py` — `list_equipos` at GET /api/equipos and `get_equipo_detail` at GET /api/equipos/detail, both guarded by `require_permission("equipos:asignar")`
- [x] 5.3 Execute tests: confirm GREEN
- [x] 5.4 TRIANGULATE: Add `test_list_equipos_403_without_permission`, `test_get_equipo_detail_returns_asignaciones`, `test_get_equipo_detail_404_not_found`
- [x] 5.5 Execute tests: confirm all pass

## 6. Equipos Router — Asignación Masiva (POST) — RED → GREEN → TRIANGULATE

- [x] 6.1 RED: Write failing integration test — `test_asignacion_masiva_201` POST /api/equipos/masiva returns 201 with list of AsignacionResponse
- [x] 6.2 GREEN: Implement `asignacion_masiva` endpoint at POST /api/equipos/masiva with `require_permission("equipos:asignar")`, calls `EquipoService.asignacion_masiva()`
- [x] 6.3 Execute tests: confirm GREEN
- [x] 6.4 TRIANGULATE: Add `test_asignacion_masiva_404_missing_usuario`, `test_asignacion_masiva_422_too_many_users`, `test_asignacion_masiva_403_without_permission`
- [x] 6.5 Execute tests: confirm all pass

## 7. Equipos Router — Clonar (POST) — RED → GREEN → TRIANGULATE

- [x] 7.1 RED: Write failing integration test — `test_clonar_equipo_201` POST /api/equipos/clonar returns 201 with EquipoDetailResponse of destination
- [x] 7.2 GREEN: Implement `clonar_equipo` endpoint at POST /api/equipos/clonar with `require_permission("equipos:asignar")`, calls `EquipoService.clonar_equipo()`
- [x] 7.3 Execute tests: confirm GREEN
- [x] 7.4 TRIANGULATE: Add `test_clonar_equipo_404_empty_origen`, `test_clonar_equipo_403_without_permission`
- [x] 7.5 Execute tests: confirm all pass

## 8. Equipos Router — Vigencia (PATCH) — RED → GREEN → TRIANGULATE

- [x] 8.1 RED: Write failing integration test — `test_modificar_vigencia_200` PATCH /api/equipos/vigencia returns 200 with updated EquipoDetailResponse
- [x] 8.2 GREEN: Implement `modificar_vigencia` endpoint at PATCH /api/equipos/vigencia with `require_permission("equipos:asignar")`, calls `EquipoService.modificar_vigencia()`
- [x] 8.3 Execute tests: confirm GREEN
- [x] 8.4 TRIANGULATE: Add `test_modificar_vigencia_422_invalid_dates`, `test_modificar_vigencia_404_not_found`, `test_modificar_vigencia_403_without_permission`
- [x] 8.5 Execute tests: confirm all pass

## 9. Equipos Router — Export (GET) — RED → GREEN → TRIANGULATE

- [x] 9.1 RED: Write failing integration test — `test_export_equipo_200_csv` GET /api/equipos/export returns 200 with text/csv content type
- [x] 9.2 GREEN: Implement `exportar_equipo` endpoint at GET /api/equipos/export with `require_permission("equipos:asignar")`, calls `EquipoService.exportar_equipo()` and returns StreamingResponse with CSV
- [x] 9.3 Execute tests: confirm GREEN
- [x] 9.4 TRIANGULATE: Add `test_export_csv_includes_header_and_data`, `test_export_equipo_404_not_found`, `test_export_equipo_403_without_permission`
- [x] 9.5 Execute tests: confirm all pass

## 10. Equipos Router — Usuario Search (GET) — RED → GREEN → TRIANGULATE

- [x] 10.1 RED: Write failing integration test — `test_search_usuarios_returns_matches` GET /api/equipos/usuarios/search?q=Martín returns UsuarioSearchResponse list
- [x] 10.2 GREEN: Implement `search_usuarios` endpoint at GET /api/equipos/usuarios/search with `require_permission("equipos:asignar")`, calls `EquipoService.buscar_usuarios()`
- [x] 10.3 Execute tests: confirm GREEN
- [x] 10.4 TRIANGULATE: Add `test_search_usuarios_by_legajo`, `test_search_usuarios_empty_no_match`, `test_search_usuarios_403_without_permission`
- [x] 10.5 Execute tests: confirm all pass

## 11. Router Registration — Main app wiring

- [x] 11.1 Register equipos router in `backend/app/main.py` under `/api/equipos`
- [x] 11.2 Verify all endpoints are accessible with correct prefix
- [x] 11.3 Execute full test suite: confirm all tests pass — 426 passed, 2 skipped
- [x] 11.4 Run linting/type-checking on all new and modified files
