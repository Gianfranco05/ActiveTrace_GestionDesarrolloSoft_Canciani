## 0. Safety Net — Pre-existing tests baseline

- [x] 0.1 Run existing test suite from `backend/`: capture "518 passed, 2 skipped" baseline
- [x] 0.2 If any test FAILS → STOP, report as pre-existing failure to orchestrator

## 1. Seed Permission + Audit Codes

- [x] 1.1 Verify `atrasados:ver` exists in the permiso catalog. If not, create it via seed script or data migration, assigned to PROFESOR, TUTOR, COORDINADOR, ADMIN roles
- [x] 1.2 Add new audit action codes to `backend/app/core/audit_codes.py`: `ANALISIS_ATRASADOS`, `ANALISIS_RANKING`, `ANALISIS_REPORTE`, `ANALISIS_NOTAS_FINALES`, `ANALISIS_EXPORT_TPS`, `ANALISIS_MONITOR`

## 2. Pydantic Schemas — Implementation

- [x] 2.1 Implement `backend/app/schemas/analisis.py` — all response DTOs: `AlumnoAtrasado`, `RankingRow`, `NotaFinalRow`, `ReporteMateria`, `TPSinCorregirRow`, `MonitorGeneralRow`, `MonitorSeguimientoRow`, `MonitorCoordinacionRow`. All with `model_config = ConfigDict(extra='forbid', from_attributes=True)`
- [x] 2.2 Write `tests/test_analisis_schemas.py` — verify serialization, extra fields rejected, default values

## 3. Atrasados Service — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test `tests/test_atrasados_service.py` — `test_detect_atrasados_por_faltantes`, expects atrasado list for materia with missing activities
- [x] 3.2 GREEN: Implement `backend/app/services/analisis/atrasados_service.py` — `AtrasadosService.get_atrasados(materia_id, cohorte_id)` queries Calificacion + EntradaPadron per D4 algorithm
- [x] 3.3 Execute tests: confirm GREEN
- [x] 3.4 TRIANGULATE: Add `test_detect_atrasados_por_nota_baja`, `test_detect_atrasados_ambos`, `test_alumno_al_dia_no_incluido`, `test_sin_calificaciones_todos_atrasados`, `test_scope_profesor_solo_sus_materias`, `test_atrasados_filter_by_materia_cohorte`
- [x] 3.5 Execute tests: confirm all pass

## 4. Ranking Service — RED → GREEN → TRIANGULATE

- [x] 4.1 RED: Write failing test `tests/test_ranking_service.py` — `test_ranking_returns_sorted_by_approved`
- [x] 4.2 GREEN: Implement `backend/app/services/analisis/ranking_service.py` — `RankingService.get_ranking(materia_id, cohorte_id)` per D5 algorithm with HAVING COUNT(*) > 0
- [x] 4.3 Execute tests: confirm GREEN
- [x] 4.4 TRIANGULATE: Add `test_ranking_excludes_zero_approved`, `test_ranking_ties_alphabetical`, `test_ranking_empty_when_no_approved`, `test_ranking_response_format`
- [x] 4.5 Execute tests: confirm all pass

## 5. Notas Finales Service — RED → GREEN → TRIANGULATE

- [x] 5.1 RED: Write failing test `tests/test_ranking_service.py` — `test_notas_finales_average`
- [x] 5.2 GREEN: Implement `NotasFinalesService.get_notas(materia_id, cohorte_id)` in ranking_service.py — average of numeric calificaciones per D6
- [x] 5.3 Execute tests: confirm GREEN
- [x] 5.4 TRIANGULATE: Add `test_notas_finales_textual_only_is_null`, `test_notas_finales_sin_datos`, `test_notas_finales_state_derivation_regular`, `test_notas_finales_state_derivation_libre`
- [x] 5.5 Execute tests: confirm all pass

## 6. Reportes Service — RED → GREEN → TRIANGULATE

- [x] 6.1 RED: Write failing test `tests/test_reportes_service.py` — `test_reporte_materia_aggregates`
- [x] 6.2 GREEN: Implement `backend/app/services/analisis/reportes_service.py` — `ReportesService.get_reporte(materia_id)` per D8 schema
- [x] 6.3 Execute tests: confirm GREEN
- [x] 6.4 TRIANGULATE: Add `test_reporte_materia_sin_datos`, `test_reporte_materia_response_format`
- [x] 6.5 Execute tests: confirm all pass

## 7. Export TPs sin corregir Service — RED → GREEN → TRIANGULATE

- [x] 7.1 RED: Write failing test `tests/test_reportes_service.py` — `test_export_tps_sin_corregir_csv`
- [x] 7.2 GREEN: Implement `ExportService.export_tps_sin_corregir(materia_id, cohorte_id)` in reportes_service.py — query textual calificaciones with null grades, generate CSV per D7
- [x] 7.3 Execute tests: confirm GREEN
- [x] 7.4 TRIANGULATE: Add `test_export_excludes_numeric_without_grade`, `test_export_excludes_graded_textual`, `test_export_empty_csv`
- [x] 7.5 Execute tests: confirm all pass

## 8. Monitor General Service — RED → GREEN → TRIANGULATE

- [x] 8.1 RED: Write failing test `tests/test_monitores_service.py` — `test_monitor_general_cross_materia`
- [x] 8.2 GREEN: Implement `MonitoresService.get_monitor_general()` in `backend/app/services/analisis/monitores_service.py` — aggregate across all materias per D9
- [x] 8.3 Execute tests: confirm GREEN
- [x] 8.4 TRIANGULATE: Add `test_monitor_general_row_format`
- [x] 8.5 Execute tests: confirm all pass

## 9. Monitor Seguimiento Service — RED → GREEN → TRIANGULATE

- [x] 9.1 RED: Write failing test `tests/test_monitores_service.py` — `test_monitor_seguimiento_scoped_to_user`
- [x] 9.2 GREEN: Implement `MonitoresService.get_seguimiento(usuario_id, materia_id=None)` — per-materia detail scoped by asignacion
- [x] 9.3 Execute tests: confirm GREEN
- [x] 9.4 TRIANGULATE: Add `test_monitor_seguimiento_filtered_by_materia`, `test_monitor_seguimiento_student_status_al_dia`, `test_monitor_seguimiento_student_status_atrasado`
- [x] 9.5 Execute tests: confirm all pass

## 10. Monitor Coordinación Service — RED → GREEN → TRIANGULATE

- [x] 10.1 RED: Write failing test `tests/test_monitores_service.py` — `test_monitor_coordinacion_date_range_filter`
- [x] 10.2 GREEN: Implement `MonitoresService.get_coordinacion(desde=None, hasta=None, materia_id=None)` — full view with date range filter
- [x] 10.3 Execute tests: confirm GREEN
- [x] 10.4 TRIANGULATE: Add `test_monitor_coordinacion_sin_filtros`, `test_monitor_coordinacion_filtered_by_materia`
- [x] 10.5 Execute tests: confirm all pass

## 11. Analisis Router — RED → GREEN → TRIANGULATE

- [x] 11.1 RED: Write failing integration test `tests/test_analisis_router.py` — `test_get_atrasados_200` GET /api/analisis/atrasados returns list for user with `atrasados:ver`
- [x] 11.2 GREEN: Implement `backend/app/api/v1/routers/analisis.py` — `analisis_router` with all 8 endpoints, guarded by `atrasados:ver`
- [x] 11.3 Register router in `backend/app/main.py` under `analisis_router`
- [x] 11.4 Execute tests: confirm GREEN
- [x] 11.5 TRIANGULATE: Add `test_get_ranking_200`, `test_get_reporte_materia_200`, `test_get_notas_finales_200`, `test_export_tps_csv_200`, `test_get_monitor_general_200`, `test_get_monitor_seguimiento_200`, `test_get_monitor_coordinacion_200`, `test_403_without_atrasados_ver`, `test_401_without_auth`
- [x] 11.6 Execute tests: confirm all pass

## 12. Full Integration Test

- [ ] 12.1 Write `test_analisis_integration.py` — full E2E: seed grades → query atrasados → query ranking → query reportes → query notas finales → export TPs CSV → monitor general → monitor seguimiento → monitor coordinacion
- [ ] 12.2 Execute full test suite: verify baseline (518 passed, 2 skipped) + new tests all green
- [ ] 12.3 Run linting/type-checking on all new and modified files