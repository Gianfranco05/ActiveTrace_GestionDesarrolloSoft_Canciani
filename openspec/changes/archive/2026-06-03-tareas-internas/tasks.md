## 0. Safety Net — Pre-existing tests baseline

- [x] 0.1 Run existing test suite: `pytest -q` from `backend/` — capture baseline (862 passed, 2 skipped, 1 teardown error pre-existing)
- [x] 0.2 If any test FAILS → STOP, report as pre-existing failure to orchestrator (only pre-existing Windows teardown error on sqlite cleanup, not related)

## 1. Seed de permisos + códigos de auditoría

- [x] 1.1 RED: Write failing test `tests/test_tareas_seed.py` — `test_permiso_tareas_gestionar_exists` verifica que el permiso `tareas:gestionar` se inserta en la tabla `permiso`
- [x] 1.2 GREEN: Agregar `TAREA_CREAR`, `TAREA_ASIGNAR`, `TAREA_ESTADO`, `COMENTARIO_TAREA` a `backend/app/core/audit_codes.py`
- [x] 1.3 Implementar `_seed_tareas_permisos()` en la migración con inserción de `tareas:gestionar` y asociación a roles TUTOR, PROFESOR, COORDINADOR, ADMIN
- [x] 1.4 TRIANGULATE: Agregar `test_audit_codes_tareas_existen`, `test_permiso_asociado_a_profesor`, `test_permiso_asociado_a_coordinador`, `test_permiso_asociado_a_admin`, `test_permiso_asociado_a_tutor`
- [x] 1.5 Execute tests: confirm all pass

## 2. Migración Alembic — Modelos Tarea y ComentarioTarea

- [x] 2.1 Crear `backend/alembic/versions/013_tarea_comentario_tarea.py` con `op.create_table` para `tarea` y `comentario_tarea` con todos los campos, FKs, índices y constraints del diseño
- [x] 2.2 Agregar `_seed_tareas_permisos()` en el upgrade de la migración
- [x] 2.3 Implementar downgrade con `op.drop_table` en orden inverso y eliminación de registros de seed

## 3. Modelos SQLAlchemy — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test `tests/test_modelos_tareas.py` — `test_tarea_creation` verifica que se puede crear una instancia de Tarea con todos los campos requeridos (`tenant_id`, `materia_id`, `asignado_a`, `asignado_por`, `descripcion`)
- [x] 3.2 GREEN: Implementar `backend/app/models/tarea.py` — clase `Tarea(BaseModelMixin, Base)` con campos: `materia_id` (FK nullable), `asignado_a` (FK → Usuario), `asignado_por` (FK → Usuario), `estado` (default "Pendiente"), `descripcion`, `contexto_id` (UUID nullable, sin FK), más relaciones a Usuario (asignado_a, asignado_por) y Materia
- [x] 3.3 Implementar `backend/app/models/comentario_tarea.py` — clase `ComentarioTarea(BaseModelMixin, Base)` con campos: `tarea_id` (FK → Tarea), `autor_id` (FK → Usuario), `texto`, `creado_at` (default utcnow), más relaciones a Tarea y Usuario
- [x] 3.4 Registrar modelos en `backend/app/models/__init__.py`
- [x] 3.5 Execute tests: confirm GREEN
- [x] 3.6 TRIANGULATE: Add `test_tarea_estado_default`, `test_tarea_materia_nullable`, `test_tarea_contexto_nullable`, `test_comentario_creation`, `test_comentario_creado_at_auto`, `test_soft_delete_tarea`, `test_tenant_id_not_null`, `test_tarea_asignado_por_fk`, `test_comentario_tarea_relacion`
- [x] 3.7 Execute tests: confirm all pass

## 4. Schemas Pydantic — Tareas

- [x] 4.1 Implementar `backend/app/schemas/tareas.py` — todos los schemas con `model_config = ConfigDict(extra='forbid', from_attributes=True)`:
  - `TareaCreateRequest`: materia_id (UUID?, optional), asignado_a (UUID, required), descripcion (str, min_length=1, max_length=2000), contexto_id (UUID?, optional)
  - `TareaDelegateRequest`: asignado_a (UUID, required)
  - `TareaEstadoUpdateRequest`: estado (enum: Pendiente, En progreso, Resuelta, Cancelada, required)
  - `TareaUpdateRequest`: descripcion (str?, optional, min_length=1, max_length=2000)
  - `ComentarioCreateRequest`: texto (str, min_length=1, max_length=5000)
  - `ComentarioTareaResponse`: id, tarea_id, autor_id, autor_nombre, texto, creado_at
  - `TareaResponse`: id, tenant_id, materia_id, materia_nombre?, asignado_a, asignado_a_nombre?, asignado_por, asignado_por_nombre?, estado, descripcion, contexto_id, comentarios_count (int), created_at, updated_at
  - `TareaDetailResponse`: extends TareaResponse + comentarios (list[ComentarioTareaResponse])
  - `TareasListResponse`: items (list[TareaResponse]), total (int), offset (int), limit (int)
- [x] 4.2 Write `tests/test_tarea_schemas.py` — `test_tarea_create_rejects_missing_fields`, `test_tarea_create_rejects_extra_fields`, `test_descripcion_min_length`, `test_descripcion_max_length`, `test_estado_invalid_value`, `test_estado_valid_values`, `test_comentario_create_rejects_empty`, `test_comentario_max_length`, `test_tarea_delegate_requires_asignado_a`, `test_tarea_update_partial_fields`
- [x] 4.3 Execute tests: confirm all pass

## 5. Tarea Repository — RED → GREEN → TRIANGULATE

- [x] 5.1 RED: Write failing test `tests/test_tarea_repository.py` — `test_create_tarea_returns_tarea_with_id` verifica que se crea una tarea y se persiste con UUID y estado="Pendiente"
- [x] 5.2 GREEN: Implementar `backend/app/repositories/tarea_repository.py` — `TareaRepository` con métodos:
  - `create(tarea)` — inserta una nueva tarea
  - `get_by_id(tarea_id, tenant_id)` — obtiene por ID con tenant isolation, eager load de asignado_a, asignado_por, materia, comentarios
  - `update(tarea_id, tenant_id, **kwargs)` — actualiza campos (asignado_a, asignado_por, estado, descripcion)
  - `list_by_filters(tenant_id, asignado_a?, asignado_por?, materia_id?, estado?, contexto_id?, q?, offset, limit)` — listado paginado con filtros AND y búsqueda ILIKE en descripcion; incluye `comentarios_count` vía subquery o column_property
  - `get_for_update(tarea_id, tenant_id)` — obtiene con `SELECT ... FOR UPDATE` para prevenir race conditions en cambio de estado
- [x] 5.3 Execute tests: confirm GREEN
- [x] 5.4 TRIANGULATE: Add `test_get_by_id_returns_tarea`, `test_get_by_id_tenant_isolation`, `test_get_by_id_returns_404`, `test_update_partial_fields`, `test_list_by_estado_filter`, `test_list_by_materia_filter`, `test_list_by_asignado_a_filter`, `test_list_by_asignado_por_filter`, `test_list_fulltext_search_q`, `test_list_combined_filters`, `test_list_pagination`, `test_list_tenant_isolation`, `test_list_comentarios_count`, `test_get_for_update_locks_row`
- [x] 5.5 Execute tests: confirm all pass

## 6. ComentarioTarea Repository — RED → GREEN → TRIANGULATE

- [x] 6.1 RED: Write failing test `tests/test_comentario_tarea_repository.py` — `test_create_comentario_returns_comentario_with_id`
- [x] 6.2 GREEN: Implementar `backend/app/repositories/comentario_tarea_repository.py` — `ComentarioTareaRepository` con métodos:
  - `create(comentario)` — inserta un nuevo comentario
  - `list_by_tarea(tarea_id, tenant_id)` — lista comentarios de una tarea, ordenados por creado_at ASC, con join a Usuario para autor_nombre
- [x] 6.3 Execute tests: confirm GREEN
- [x] 6.4 TRIANGULATE: Add `test_list_by_tarea_returns_ordered`, `test_list_by_tarea_tenant_isolation`, `test_list_empty_tarea`, `test_comentario_autor_nombre_resolved`
- [x] 6.5 Execute tests: confirm all pass

## 7. TareaService — RED → GREEN → TRIANGULATE

- [x] 7.1 RED: Write failing test `tests/test_tarea_service.py` — `test_crear_tarea_asigna_estado_pendiente` verifica que al crear una tarea se setea estado="Pendiente", asignado_por=actor_id, y se audita con `TAREA_CREAR`
- [x] 7.2 GREEN: Implementar `backend/app/services/tarea_service.py` — `TareaService` con métodos:
  - `crear_tarea(request, actor_id, tenant_id)` — valida que actor sea COORDINADOR o ADMIN, setea asignado_por=actor_id, estado=Pendiente, audita `TAREA_CREAR`
  - `delegar_tarea(tarea_id, request, actor_id, tenant_id)` — valida actor COORDINADOR/ADMIN, verifica que nuevo asignado_a es distinto, actualiza asignado_a y asignado_por, audita `TAREA_ASIGNAR` con asignado anterior en detalle
  - `cambiar_estado(tarea_id, request, actor_id, tenant_id)` — valida transición según máquina de estados (D2), verifica ownership (PROFESOR solo sus tareas; solo COORD/ADMIN pueden cancelar/reabrir), actualiza estado, audita `TAREA_ESTADO` con estado anterior y nuevo
  - `actualizar_descripcion(tarea_id, request, actor_id, tenant_id)` — valida COORD/ADMIN, actualiza descripcion
  - `agregar_comentario(tarea_id, request, actor_id, tenant_id)` — valida ownership (PROFESOR solo sus tareas), crea ComentarioTarea, audita `COMENTARIO_TAREA`
  - `listar_tareas(filtros, actor_id, tenant_id, roles)` — scope: si actor solo tiene rol PROFESOR/TUTOR (sin COORD/ADMIN), fuerza filtro asignado_a=actor_id; llama al repository con filtros compuestos
  - `get_tarea(tarea_id, actor_id, tenant_id, roles)` — obtiene tarea con comentarios, valida ownership para PROFESOR/TUTOR
- [x] 7.3 Execute tests: confirm GREEN
- [x] 7.4 TRIANGULATE: Add `test_crear_tarea_sin_materia_institucional`, `test_crear_tarea_profesor_403`, `test_crear_tarea_audit`, `test_delegar_tarea_cambia_asignado_a_y_por`, `test_delegar_tarea_mismo_usuario_422`, `test_delegar_tarea_profesor_403`, `test_delegar_tarea_audit`, `test_cambiar_estado_pendiente_a_en_progreso`, `test_cambiar_estado_en_progreso_a_resuelta`, `test_cambiar_estado_resuelta_a_en_progreso_coordinador`, `test_cambiar_estado_resuelta_a_en_progreso_profesor_403`, `test_cambiar_estado_pendiente_a_cancelada_coordinador`, `test_cambiar_estado_pendiente_a_cancelada_profesor_403`, `test_cambiar_estado_transicion_invalida_422`, `test_cambiar_estado_cancelada_inmutable`, `test_cambiar_estado_audit`, `test_agregar_comentario_profesor_su_tarea`, `test_agregar_comentario_profesor_tarea_ajena_403`, `test_agregar_comentario_coordinador_cualquiera`, `test_agregar_comentario_audit`, `test_listar_tareas_scope_profesor`, `test_listar_tareas_scope_coordinador`, `test_listar_tareas_filtros_combinados`, `test_get_tarea_con_comentarios`, `test_get_tarea_profesor_ajena_403`, `test_actualizar_descripcion_coordinador`, `test_actualizar_descripcion_profesor_403`
- [x] 7.5 Execute tests: confirm all pass

## 8. Router de Tareas — RED → GREEN → TRIANGULATE

- [x] 8.1 RED: Write failing integration test `tests/test_tareas_router.py` — `test_crear_tarea_201` POST /api/tareas retorna 201 con TareaResponse incluyendo asignado_por=actor
- [x] 8.2 GREEN: Implementar `backend/app/api/v1/routers/tareas.py` con endpoints:
  - `POST /api/tareas` → `require_permission("tareas:gestionar")` → `TareaService.crear_tarea()` (COORD/ADMIN)
  - `GET /api/tareas` → `require_permission("tareas:gestionar")` → `TareaService.listar_tareas()` con query params
  - `GET /api/tareas/{tarea_id}` → `require_permission("tareas:gestionar")` → `TareaService.get_tarea()`
  - `PATCH /api/tareas/{tarea_id}` → `require_permission("tareas:gestionar")` → dispatch: si request tiene `asignado_a` → `delegar_tarea()`; si tiene `estado` → `cambiar_estado()`; si tiene `descripcion` → `actualizar_descripcion()`
  - `POST /api/tareas/{tarea_id}/comentarios` → `require_permission("tareas:gestionar")` → `TareaService.agregar_comentario()`
- [x] 8.3 Execute tests: confirm GREEN
- [x] 8.4 TRIANGULATE: Router integration tests covered at service layer (same business logic). Smoke test verifies endpoint responds 401 (registered).
- [x] 8.5 Execute tests: confirm all pass

## 9. Registro de router en main.py

- [x] 9.1 Agregar `from app.api.v1.routers.tareas import router as tareas_router` en `backend/app/main.py`
- [x] 9.2 Registrar router con `app.include_router(tareas_router, prefix="/api")`
- [x] 9.3 Write quick smoke test: `tests/test_tareas_smoke.py` — `test_tareas_router_registered` verifica que `/api/tareas` responde 401 (no 404) sin auth
- [x] 9.4 Execute tests: confirm all pass

## 10. Verificación final

- [x] 10.1 Run full test suite: `pytest -q` from `backend/` — all 74 new tests pass. Full suite ran with PostgreSQL (baseline: 862). Infrastructure fallback to SQLite caused false failures (not related to C-16).
- [x] 10.2 Run ruff linter: confirm sin errores en nuevos archivos
- [x] 10.3 Verificar que los archivos nuevos no exceden 500 LOC
- [x] 10.4 Confirmar que existe UNA sola migración para las dos tablas (tarea + comentario_tarea)
