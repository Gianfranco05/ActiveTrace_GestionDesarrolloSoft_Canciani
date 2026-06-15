## 0. Safety Net — Pre-existing tests baseline

- [x] 0.1 Run existing test suite: capture baseline (e.g. "N tests passing")
- [x] 0.2 If any test FAILS → STOP, report as pre-existing failure to orchestrator

## 1. Seed de permisos + códigos de auditoría

- [x] 1.1 RED: Write failing test `tests/test_encuentros_seed.py` — `test_permiso_encuentros_gestionar_exists` verifica que el permiso `encuentros:gestionar` se inserta en la tabla `permiso`
- [x] 1.2 GREEN: Agregar `ENCUENTRO_CREAR`, `ENCUENTRO_EDITAR`, `GUARDIA_REGISTRAR` a `backend/app/core/audit_codes.py`
- [x] 1.3 Implementar `_seed_encuentros_permisos()` en la migración (grupo 2) con inserción de `encuentros:gestionar` y asociación a roles PROFESOR, COORDINADOR, ADMIN
- [x] 1.4 TRIANGULATE: Agregar `test_audit_codes_encuentros_existen`, `test_permiso_asociado_a_profesor`, `test_permiso_asociado_a_coordinador`, `test_permiso_asociado_a_admin`
- [x] 1.5 Execute tests: confirm all pass

## 2. Migración Alembic — Modelos SlotEncuentro, InstanciaEncuentro, Guardia

- [x] 2.1 Crear `backend/alembic/versions/009_slot_encuentro_instancia_guardia.py` con `op.create_table` para `slot_encuentro`, `instancia_encuentro`, `guardia` con todos los campos, FKs, índices y constraints del diseño
- [x] 2.2 Agregar `_seed_encuentros_permisos()` en el upgrade de la migración
- [x] 2.3 Implementar downgrade con `op.drop_table` en orden inverso y eliminación de registros de seed

## 3. Modelos SQLAlchemy — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test `tests/test_modelos_encuentros.py` — `test_slot_encuentro_creation` verifica que se puede crear una instancia de SlotEncuentro con todos los campos requeridos
- [x] 3.2 GREEN: Implementar `backend/app/models/slot_encuentro.py` — clase `SlotEncuentro(BaseModelMixin, Base)` con campos: `asignacion_id`, `materia_id`, `titulo`, `hora`, `dia_semana`, `fecha_inicio`, `cant_semanas`, `fecha_unica`, `meet_url`, `vig_desde`, `vig_hasta`, más relaciones a Materia y Asignacion
- [x] 3.3 Implementar `backend/app/models/instancia_encuentro.py` — clase `InstanciaEncuentro(BaseModelMixin, Base)` con campos: `slot_id` (nullable), `materia_id`, `fecha`, `hora`, `titulo`, `estado`, `meet_url`, `video_url`, `comentario`
- [x] 3.4 Implementar `backend/app/models/guardia.py` — clase `Guardia(BaseModelMixin, Base)` con campos: `asignacion_id`, `materia_id`, `carrera_id`, `cohorte_id`, `dia`, `horario`, `estado`, `comentarios`, `creada_at`
- [x] 3.5 Execute tests: confirm GREEN
- [x] 3.6 TRIANGULATE: Add `test_instancia_encuentro_creation`, `test_instancia_slot_nullable`, `test_instancia_estado_default`, `test_guardia_creation`, `test_guardia_estado_default`, `test_soft_delete_slot`, `test_tenant_id_not_null`
- [x] 3.7 Execute tests: confirm all pass

## 4. Schemas Pydantic — Encuentros

- [x] 4.1 Implementar `backend/app/schemas/encuentros.py` — todos los schemas con `model_config = ConfigDict(extra='forbid', from_attributes=True)`:
  - `SlotRecurrenteCreateRequest`: materia_id, asignacion_id, titulo, hora, dia_semana (enum), fecha_inicio, cant_semanas (1-52), meet_url?
  - `SlotUnicoCreateRequest`: materia_id, asignacion_id, titulo, hora, fecha_unica, meet_url?
  - `SlotEncuentroResponse`: id, materia_id, asignacion_id, titulo, hora, dia_semana, fecha_inicio, cant_semanas, fecha_unica, meet_url, vig_desde, vig_hasta, instancias (list[InstanciaEncuentroResponse]), created_at, updated_at
  - `InstanciaUnicaCreateRequest`: materia_id, asignacion_id, titulo, fecha, hora, meet_url?
  - `InstanciaUpdateRequest`: estado?, meet_url?, video_url?, comentario?
  - `InstanciaEncuentroResponse`: id, slot_id, materia_id, fecha, hora, titulo, estado, meet_url, video_url, comentario, created_at, updated_at
  - `HtmlResponse`: html (str)
  - `EncuentrosListResponse`: items, total, offset, limit
- [x] 4.2 Write `tests/test_encuentro_schemas.py` — `test_slot_recurrente_rejects_missing_fields`, `test_slot_recurrente_rejects_extra_fields`, `test_cant_semanas_min_1`, `test_cant_semanas_max_52`, `test_dia_semana_invalid`, `test_instancia_update_partial`, `test_instancia_update_rejects_invalid_estado`
- [x] 4.3 Execute tests: confirm all pass

## 5. Schemas Pydantic — Guardias

- [x] 5.1 Implementar `backend/app/schemas/guardias.py` — todos los schemas con `model_config = ConfigDict(extra='forbid', from_attributes=True)`:
  - `GuardiaCreateRequest`: asignacion_id, materia_id, carrera_id, cohorte_id, dia (enum), horario, comentarios?
  - `GuardiaUpdateRequest`: estado?, comentarios?
  - `GuardiaResponse`: id, asignacion_id, materia_id, carrera_id, cohorte_id, dia, horario, estado, comentarios, creada_at, materia_nombre?, carrera_nombre?, cohorte_nombre?
  - `GuardiasListResponse`: items, total, offset, limit
- [x] 5.2 Write `tests/test_guardia_schemas.py` — `test_guardia_create_rejects_missing_fields`, `test_guardia_create_rejects_extra_fields`, `test_dia_invalid`, `test_guardia_update_partial`
- [x] 5.3 Execute tests: confirm all pass

## 6. SlotEncuentro Repository — RED → GREEN → TRIANGULATE

- [x] 6.1 RED: Write failing test `tests/test_slot_encuentro_repository.py` — `test_create_slot_returns_slot_with_id` verifica que se crea un slot y se persiste con UUID
- [x] 6.2 GREEN: Implementar `backend/app/repositories/slot_encuentro_repository.py` — `SlotEncuentroRepository` con métodos: `create(slot)`, `get_by_id(id, tenant_id)`, `list_by_materia(materia_id, tenant_id, asignacion_id?, offset, limit)`, `list_by_asignacion(asignacion_id, tenant_id)`, `soft_delete(id, tenant_id)`
- [x] 6.3 Execute tests: confirm GREEN
- [x] 6.4 TRIANGULATE: Add `test_get_by_id_returns_slot`, `test_get_by_id_tenant_isolation`, `test_list_by_materia_returns_filtered`, `test_list_by_asignacion_scope_profesor`, `test_soft_delete_sets_timestamp`, `test_soft_delete_idempotent`
- [x] 6.5 Execute tests: confirm all pass

## 7. InstanciaEncuentro Repository — RED → GREEN → TRIANGULATE

- [x] 7.1 RED: Write failing test `tests/test_instancia_encuentro_repository.py` — `test_create_instancia_returns_instancia_with_id`
- [x] 7.2 GREEN: Implementar `backend/app/repositories/instancia_encuentro_repository.py` — `InstanciaEncuentroRepository` con métodos: `create(instancia)`, `bulk_create(instancias: list)`, `get_by_id(id, tenant_id)`, `update(id, tenant_id, **kwargs)`, `list_by_slot(slot_id, tenant_id)`, `list_by_filters(materia_id?, slot_id?, estado?, tenant_id, offset, limit)`, `list_by_asignacion(asignacion_id, tenant_id)`
- [x] 7.3 Execute tests: confirm GREEN
- [x] 7.4 TRIANGULATE: Add `test_bulk_create_creates_all`, `test_bulk_create_transactional`, `test_update_partial_fields`, `test_list_by_estado_filter`, `test_list_by_slot_returns_sorted`, `test_tenant_isolation`
- [x] 7.5 Execute tests: confirm all pass

## 8. Guardia Repository — RED → GREEN → TRIANGULATE

- [x] 8.1 RED: Write failing test `tests/test_guardia_repository.py` — `test_create_guardia_returns_guardia_with_id`
- [x] 8.2 GREEN: Implementar `backend/app/repositories/guardia_repository.py` — `GuardiaRepository` con métodos: `create(guardia)`, `get_by_id(id, tenant_id)`, `update(id, tenant_id, **kwargs)`, `list_by_filters(materia_id?, carrera_id?, cohorte_id?, dia?, estado?, tenant_id, asignacion_id?, offset, limit)`, `list_for_export(materia_id?, carrera_id?, cohorte_id?, dia?, estado?, tenant_id, asignacion_id?)`
- [x] 8.3 Execute tests: confirm GREEN
- [x] 8.4 TRIANGULATE: Add `test_update_partial`, `test_list_filtered_by_materia`, `test_list_filtered_by_estado`, `test_list_filtered_by_dia`, `test_list_for_export_returns_all_matching`, `test_tutor_scope_only_own`
- [x] 8.5 Execute tests: confirm all pass

## 9. SlotService — RED → GREEN → TRIANGULATE

- [x] 9.1 RED: Write failing test `tests/test_slot_service.py` — `test_crear_slot_recurrente_genera_instancias` verifica que al crear un slot recurrente con cant_semanas=4 se generan 4 instancias con fechas correctas
- [x] 9.2 GREEN: Implementar `backend/app/services/slot_service.py` — `SlotService` con métodos:
  - `crear_slot_recurrente(request, actor_id)` — valida asignacion_id pertenece al actor (o actor es COORDINADOR/ADMIN), calcula fechas de instancias, crea slot + bulk_create instancias en transacción, audita `ENCUENTRO_CREAR`
  - `crear_slot_unico(request, actor_id)` — crea slot con fecha_unica + 1 instancia, audita `ENCUENTRO_CREAR`
  - `listar_slots(materia_id?, cohorte_id?, actor_id, tenant_id, offset, limit)` — scope por asignacion para PROFESOR
  - `get_slot(slot_id, tenant_id)` — obtiene slot con sus instancias
  - `soft_delete_slot(slot_id, tenant_id, actor_id)` — soft delete, no afecta instancias
- [x] 9.3 Execute tests: confirm GREEN
- [x] 9.4 TRIANGULATE: Add `test_calculo_fecha_inicio_distinto_dia_semana`, `test_cant_semanas_1_genera_1_instancia`, `test_crear_slot_unico_genera_1_instancia`, `test_profesor_no_puede_usar_asignacion_ajena`, `test_audit_slot_recurrente`, `test_audit_slot_unico`, `test_soft_delete_no_borra_instancias`
- [x] 9.5 Execute tests: confirm all pass

## 10. EncuentroService — RED → GREEN → TRIANGULATE

- [x] 10.1 RED: Write failing test `tests/test_encuentro_service.py` — `test_editar_instancia_cambia_estado` verifica que se actualiza el estado de una instancia y se audita
- [x] 10.2 GREEN: Implementar `backend/app/services/encuentro_service.py` — `EncuentroService` con métodos:
  - `crear_instancia_unica(request, actor_id)` — crea instancia independiente (slot_id=null), audita `ENCUENTRO_CREAR`
  - `editar_instancia(instancia_id, request, actor_id)` — partial update de estado/meet_url/video_url/comentario, valida ownership (PROFESOR solo propias), audita `ENCUENTRO_EDITAR`
  - `listar_instancias(materia_id?, slot_id?, estado?, actor_id, tenant_id, offset, limit)` — scope por asignacion para PROFESOR
  - `generar_html_slot(slot_id, tenant_id)` — genera bloque HTML con instancias ordenadas por fecha, inline styles, links a meet_url y video_url, marca canceladas
- [x] 10.3 Execute tests: confirm GREEN
- [x] 10.4 TRIANGULATE: Add `test_editar_solo_campos_permitidos`, `test_editar_instancia_ajena_profesor_403`, `test_coordinador_puede_editar_cualquiera`, `test_generar_html_incluye_todas_instancias`, `test_generar_html_canceladas_marcadas`, `test_generar_html_video_url_link`, `test_crear_instancia_unica_audit`, `test_editar_instancia_audit`
- [x] 10.5 Execute tests: confirm all pass

## 11. GuardiaService — RED → GREEN → TRIANGULATE

- [x] 11.1 RED: Write failing test `tests/test_guardia_service.py` — `test_registrar_guardia_crea_con_estado_pendiente` verifica que se crea una guardia con estado Pendiente y se audita
- [x] 11.2 GREEN: Implementar `backend/app/services/guardia_service.py` — `GuardiaService` con métodos:
  - `registrar_guardia(request, actor_id)` — valida asignacion_id pertenece al actor (TUTOR solo propia; COORDINADOR/ADMIN cualquier), crea guardia con estado Pendiente, audita `GUARDIA_REGISTRAR`
  - `editar_guardia(guardia_id, request, actor_id)` — partial update, valida ownership
  - `listar_guardias(filtros, actor_id, tenant_id)` — scope TUTOR: solo propias; COORDINADOR/ADMIN: todas
  - `exportar_guardias(filtros, actor_id, tenant_id)` — genera CSV con headers
- [x] 11.3 Execute tests: confirm GREEN
- [x] 11.4 TRIANGULATE: Add `test_tutor_no_puede_registrar_guardia_ajena`, `test_coordinador_puede_registrar_para_cualquiera`, `test_editar_guardia_audit`, `test_listar_guardias_scope_tutor`, `test_listar_guardias_scope_coordinador`, `test_exportar_csv_tiene_headers`, `test_exportar_csv_con_datos`, `test_exportar_csv_sin_datos`
- [x] 11.5 Execute tests: confirm all pass

## 12. Router de Encuentros — RED → GREEN → TRIANGULATE

- [x] 12.1 RED: Write failing integration test `tests/test_encuentros_router.py` — `test_crear_slot_recurrente_201` POST /api/encuentros/slots retorna 201 con SlotEncuentroResponse incluyendo instancias
- [x] 12.2 GREEN: Implementar `backend/app/api/v1/routers/encuentros.py` con endpoints:
  - `POST /api/encuentros/slots` → `require_permission("encuentros:gestionar")` → `SlotService.crear_slot_recurrente()`
  - `POST /api/encuentros/instancias` → `require_permission("encuentros:gestionar")` → `EncuentroService.crear_instancia_unica()`
  - `GET /api/encuentros/slots` → `require_permission("encuentros:gestionar")` → `SlotService.listar_slots()`
  - `GET /api/encuentros/instancias` → `require_permission("encuentros:gestionar")` → `EncuentroService.listar_instancias()`
  - `PATCH /api/encuentros/instancias/{instancia_id}` → `require_permission("encuentros:gestionar")` → `EncuentroService.editar_instancia()`
  - `GET /api/encuentros/slots/{slot_id}/html` → `require_permission("encuentros:gestionar")` → `EncuentroService.generar_html_slot()`
  - `DELETE /api/encuentros/slots/{slot_id}` → `require_permission("encuentros:gestionar")` → `SlotService.soft_delete_slot()`
- [x] 12.3 Execute tests: confirm GREEN
- [x] 12.4 TRIANGULATE: Add `test_crear_slot_recurrente_403_sin_permiso`, `test_crear_slot_recurrente_422_cant_semanas_invalida`, `test_crear_encuentro_unico_201`, `test_listar_slots_200`, `test_listar_instancias_filtro_estado`, `test_editar_instancia_200`, `test_editar_instancia_404`, `test_editar_instancia_403_cross_profesor`, `test_generar_html_200`, `test_generar_html_404`, `test_delete_slot_204`, `test_delete_slot_404`, `test_tenant_isolation_list`
- [x] 12.5 Execute tests: confirm all pass

## 13. Router de Guardias — RED → GREEN → TRIANGULATE

- [x] 13.1 RED: Write failing integration test `tests/test_guardias_router.py` — `test_registrar_guardia_201` POST /api/guardias retorna 201 con GuardiaResponse
- [x] 13.2 GREEN: Implementar `backend/app/api/v1/routers/guardias.py` con endpoints:
  - `POST /api/guardias` → `require_permission("encuentros:gestionar")` → `GuardiaService.registrar_guardia()`
  - `GET /api/guardias` → `require_permission("encuentros:gestionar")` → `GuardiaService.listar_guardias()`
  - `PATCH /api/guardias/{guardia_id}` → `require_permission("encuentros:gestionar")` → `GuardiaService.editar_guardia()`
  - `GET /api/guardias/export` → `require_permission("encuentros:gestionar")` → `GuardiaService.exportar_guardias()` con StreamingResponse text/csv
- [x] 13.3 Execute tests: confirm GREEN
- [x] 13.4 TRIANGULATE: Add `test_registrar_guardia_403_sin_permiso`, `test_registrar_guardia_422_faltan_campos`, `test_listar_guardias_200`, `test_listar_guardias_filtro_materia`, `test_listar_guardias_scope_tutor`, `test_editar_guardia_200`, `test_editar_guardia_403_cross_tutor`, `test_export_guardias_csv`, `test_export_guardias_403`, `test_tenant_isolation`
- [x] 13.5 Execute tests: confirm all pass

## 14. Registro de routers en main.py

- [x] 14.1 Agregar `from app.api.v1.routers.encuentros import router as encuentros_router` en `backend/app/main.py`
- [x] 14.2 Agregar `from app.api.v1.routers.guardias import router as guardias_router` en `backend/app/main.py`
- [x] 14.3 Registrar ambos routers con `app.include_router(..., prefix="/api")`
- [x] 14.4 Write quick smoke test: `tests/test_encuentros_guardias_smoke.py` — `test_routers_registered` verifica que `/api/encuentros/slots` y `/api/guardias` responden 401 (no 404) sin auth
- [x] 14.5 Execute tests: confirm all pass

## 15. Verificación final

- [x] 15.1 Run full test suite: `pytest -q` — todos los tests deben pasar
- [x] 15.2 Run ruff linter: confirm sin errores en nuevos archivos
- [x] 15.3 Verificar que los archivos nuevos no exceden 500 LOC
- [x] 15.4 Confirmar que existe UNA sola migración para las tres tablas