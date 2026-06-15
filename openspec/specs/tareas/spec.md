# tareas Specification

## Purpose
Workflow de tareas internas entre roles del equipo docente y de coordinación. Permite crear, asignar, delegar, dar seguimiento y resolver tareas con trazabilidad completa de asignador y asignado, comentarios en hilo y filtros por docente, materia y estado.

## ADDED Requirements

### Requirement: Crear tarea y asignar a docente (F8.2)

The system SHALL allow COORDINADOR and ADMIN to create a Tarea and assign it to a specific user. PROFESOR and TUTOR SHALL NOT be able to create tasks.

- Method: POST
- Path: `/api/tareas`
- Guard: `require_permission("tareas:gestionar")`
- Request body: `TareaCreateRequest` with `materia_id` (UUID?, optional — null if institutional task), `asignado_a` (UUID, required — the user who must resolve), `descripcion` (str, required, max 2000), `contexto_id` (UUID?, optional — reference to another domain entity)
- Response 201: `TareaResponse` with `id`, `tenant_id`, `materia_id`, `asignado_a`, `asignado_por` (set to authenticated user), `estado` (default "Pendiente"), `descripcion`, `contexto_id`, `created_at`, `updated_at`
- The system SHALL set `asignado_por` to the authenticated user ID
- The system SHALL set estado to "Pendiente" on creation
- The system SHALL audit the operation with `TAREA_CREAR`
- Only COORDINADOR and ADMIN roles SHALL be able to create tasks

#### Scenario: COORDINADOR crea tarea exitosamente
- **WHEN** a COORDINADOR sends POST /api/tareas with valid `asignado_a`, `materia_id`, and `descripcion`
- **THEN** the system SHALL create a Tarea with estado="Pendiente" and `asignado_por` set to the COORDINADOR's user ID
- **AND** respond 201 with the created Tarea

#### Scenario: PROFESOR no puede crear tareas
- **WHEN** a PROFESOR sends POST /api/tareas with valid data
- **THEN** the system SHALL respond 403 Forbidden

#### Scenario: Crear tarea sin materia (institucional)
- **WHEN** a COORDINADOR sends POST /api/tareas without `materia_id`
- **THEN** the system SHALL create a Tarea with `materia_id=null` and estado="Pendiente"
- **AND** respond 201

#### Scenario: Crear tarea con campos requeridos faltantes
- **WHEN** POST /api/tareas omits `asignado_a`
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Crear tarea con asignado_a inexistente
- **WHEN** POST /api/tareas references a non-existent user as `asignado_a`
- **THEN** the system SHALL respond 404 Not Found

### Requirement: Listar mis tareas (F8.1)

The system SHALL provide an endpoint for authenticated users to list tasks relevant to their role. PROFESOR and TUTOR SHALL only see tasks assigned to them. COORDINADOR and ADMIN SHALL see all tasks in the tenant.

- Method: GET
- Path: `/api/tareas`
- Guard: `require_permission("tareas:gestionar")`
- Query params: `asignado_a` (UUID?, optional filter — COORDINADOR/ADMIN only), `asignado_por` (UUID?, optional), `materia_id` (UUID?, optional), `estado` (enum?, optional: Pendiente, En progreso, Resuelta, Cancelada), `contexto_id` (UUID?, optional), `q` (str?, optional — free text search on descripcion), `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[TareaResponse], "total": int, "offset": int, "limit": int}`
- Each TareaResponse SHALL include `comentarios_count` (int) and `asignado_a_nombre`, `asignado_por_nombre`, `materia_nombre` resolved via joins
- PROFESOR/TUTOR scope: the `asignado_a` filter SHALL be forced to the authenticated user ID, regardless of query params
- COORDINADOR/ADMIN scope: all tasks in the tenant, filterable by any parameter

#### Scenario: PROFESOR ve solo sus tareas
- **WHEN** a PROFESOR calls GET /api/tareas
- **THEN** the system SHALL return only tasks where `asignado_a` equals the PROFESOR's user ID
- **AND** ignore any `asignado_a` query param if provided

#### Scenario: COORDINADOR ve todas las tareas del tenant
- **WHEN** a COORDINADOR calls GET /api/tareas
- **THEN** the system SHALL return all tasks in the tenant

#### Scenario: Filtrar tareas por estado
- **WHEN** a COORDINADOR calls GET /api/tareas?estado=Pendiente
- **THEN** the system SHALL return only tasks with estado "Pendiente"

#### Scenario: Filtrar tareas por materia
- **WHEN** a COORDINADOR calls GET /api/tareas?materia_id=<uuid>
- **THEN** the system SHALL return only tasks for that materia

#### Scenario: Filtrar tareas por docente asignado
- **WHEN** a COORDINADOR calls GET /api/tareas?asignado_a=<uuid>
- **THEN** the system SHALL return only tasks assigned to that user

#### Scenario: Búsqueda libre en descripción
- **WHEN** a COORDINADOR calls GET /api/tareas?q=seguimiento
- **THEN** the system SHALL return tasks whose `descripcion` contains "seguimiento" (case-insensitive)

#### Scenario: Combinar múltiples filtros
- **WHEN** a COORDINADOR calls GET /api/tareas?estado=En progreso&materia_id=<uuid>&asignado_a=<uuid>
- **THEN** the system SHALL return tasks matching ALL filters (AND logic)

#### Scenario: Listar tareas sin permisos
- **WHEN** an ALUMNO calls GET /api/tareas
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Obtener detalle de tarea con comentarios

The system SHALL provide an endpoint to get a single Tarea with its full comment thread.

- Method: GET
- Path: `/api/tareas/{tarea_id}`
- Guard: `require_permission("tareas:gestionar")`
- Response 200: `TareaDetailResponse` with all Tarea fields plus `comentarios: list[ComentarioTareaResponse]` ordered by `creado_at` ascending
- Each ComentarioTareaResponse SHALL include `id`, `tarea_id`, `autor_id`, `autor_nombre`, `texto`, `creado_at`
- PROFESOR/TUTOR SHALL only access tasks where they are the `asignado_a`
- COORDINADOR/ADMIN SHALL access any task in the tenant

#### Scenario: Obtener tarea con comentarios
- **WHEN** a PROFESOR calls GET /api/tareas/<id> for a task assigned to them
- **THEN** the system SHALL return the Tarea with all its ComentarioTarea records ordered by created_at

#### Scenario: Obtener tarea ajena como PROFESOR
- **WHEN** a PROFESOR calls GET /api/tareas/<id> for a task assigned to another user
- **THEN** the system SHALL respond 403 Forbidden

#### Scenario: Obtener tarea inexistente
- **WHEN** any user calls GET /api/tareas/<non-existent-id>
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: COORDINADOR puede ver cualquier tarea
- **WHEN** a COORDINADOR calls GET /api/tareas/<id> for any task in the tenant
- **THEN** the system SHALL return the Tarea with its comments

### Requirement: Delegar tarea a otro docente (F8.2)

The system SHALL allow COORDINADOR and ADMIN to reassign a task to a different user. This operation SHALL preserve traceability of who delegated and to whom.

- Method: PATCH
- Path: `/api/tareas/{tarea_id}`
- Guard: `require_permission("tareas:gestionar")`
- Request body: `TareaDelegateRequest` with `asignado_a` (UUID, required — the new assignee)
- Response 200: `TareaResponse` with updated `asignado_a` and `asignado_por`
- The system SHALL update `asignado_a` to the new user and `asignado_por` to the authenticated user
- The system SHALL audit the operation with `TAREA_ASIGNAR`, including the previous `asignado_a` in the detalle
- Only COORDINADOR and ADMIN SHALL delegate tasks

#### Scenario: COORDINADOR delega tarea a otro docente
- **WHEN** a COORDINADOR sends PATCH /api/tareas/<id> with `asignado_a: <new-user-uuid>`
- **THEN** the system SHALL update `asignado_a` to the new user and `asignado_por` to the COORDINADOR
- **AND** respond 200 with the updated Tarea

#### Scenario: Delegar tarea al mismo usuario
- **WHEN** a COORDINADOR sends PATCH with `asignado_a` equal to the current `asignado_a`
- **THEN** the system SHALL respond 422 Unprocessable Entity with message "La tarea ya está asignada a este usuario"

#### Scenario: PROFESOR intenta delegar
- **WHEN** a PROFESOR sends PATCH /api/tareas/<id> with a new `asignado_a`
- **THEN** the system SHALL respond 403 Forbidden

#### Scenario: Delegar a usuario inexistente
- **WHEN** PATCH /api/tareas/<id> references a non-existent user as `asignado_a`
- **THEN** the system SHALL respond 404 Not Found

### Requirement: Cambiar estado de tarea (workflow F8.3)

The system SHALL allow changing the estado of a Tarea following the defined state machine. Different roles have different permissions on state transitions.

- Method: PATCH
- Path: `/api/tareas/{tarea_id}`
- Guard: `require_permission("tareas:gestionar")`
- Request body: `TareaEstadoUpdateRequest` with `estado` (enum, required: Pendiente, En progreso, Resuelta, Cancelada)
- Response 200: `TareaResponse` with updated estado

Valid transitions (validated in the service layer):
- Pendiente → En progreso (by PROFESOR/TUTOR assigned, or COORDINADOR/ADMIN)
- Pendiente → Cancelada (by COORDINADOR/ADMIN only)
- En progreso → Resuelta (by PROFESOR/TUTOR assigned, or COORDINADOR/ADMIN)
- En progreso → Cancelada (by COORDINADOR/ADMIN only)
- Resuelta → En progreso (by COORDINADOR/ADMIN only — reopening)

Invalid transitions SHALL respond 422 with a message indicating the current state and valid next states.

The system SHALL audit estado changes with `TAREA_ESTADO`, including previous and new estado in the detalle.

#### Scenario: PROFESOR inicia tarea (Pendiente → En progreso)
- **WHEN** a PROFESOR assigned to a Pendiente task sends PATCH /api/tareas/<id> with `estado: En progreso`
- **THEN** the task estado SHALL change to "En progreso"
- **AND** the system SHALL audit the operation

#### Scenario: PROFESOR resuelve tarea (En progreso → Resuelta)
- **WHEN** a PROFESOR assigned to an En progreso task sends PATCH with `estado: Resuelta`
- **THEN** the task estado SHALL change to "Resuelta"
- **AND** the system SHALL audit the operation

#### Scenario: COORDINADOR cancela tarea (Pendiente → Cancelada)
- **WHEN** a COORDINADOR sends PATCH /api/tareas/<id> with `estado: Cancelada` on a Pendiente task
- **THEN** the task estado SHALL change to "Cancelada"

#### Scenario: COORDINADOR reabre tarea resuelta (Resuelta → En progreso)
- **WHEN** a COORDINADOR sends PATCH with `estado: En progreso` on a Resuelta task
- **THEN** the task estado SHALL change to "En progreso" (reopening for adjustments, FL-05 step 7)

#### Scenario: Transición inválida (Resuelta → Pendiente)
- **WHEN** any user tries to change a Resuelta task to Pendiente
- **THEN** the system SHALL respond 422 Unprocessable Entity with message indicating valid transitions

#### Scenario: Transición inválida (Cancelada → cualquier cosa)
- **WHEN** any user tries to change a Cancelada task to any other estado
- **THEN** the system SHALL respond 422 Unprocessable Entity with message "Una tarea cancelada no puede cambiar de estado"

#### Scenario: PROFESOR intenta cancelar tarea
- **WHEN** a PROFESOR tries to change a task to "Cancelada"
- **THEN** the system SHALL respond 403 Forbidden (only COORDINADOR/ADMIN can cancel)

#### Scenario: PROFESOR cambia estado de tarea no asignada
- **WHEN** a PROFESOR tries to change estado of a task not assigned to them
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Agregar comentario a tarea (workflow F8.3)

The system SHALL allow users with `tareas:gestionar` to add comments to a task's thread. Comments are append-only and cannot be edited or deleted.

- Method: POST
- Path: `/api/tareas/{tarea_id}/comentarios`
- Guard: `require_permission("tareas:gestionar")`
- Request body: `ComentarioCreateRequest` with `texto` (str, required, max 5000)
- Response 201: `ComentarioTareaResponse` with `id`, `tarea_id`, `autor_id`, `autor_nombre`, `texto`, `creado_at`
- The system SHALL set `autor_id` to the authenticated user
- The system SHALL set `creado_at` to the current timestamp
- The system SHALL audit the operation with `COMENTARIO_TAREA`
- PROFESOR/TUTOR SHALL only comment on tasks assigned to them
- COORDINADOR/ADMIN SHALL comment on any task in the tenant
- Comments SHALL NOT be editable or deletable (no PATCH/DELETE endpoints)

#### Scenario: PROFESOR agrega comentario a su tarea
- **WHEN** a PROFESOR sends POST /api/tareas/<id>/comentarios with `texto: "Revisé el caso, necesito más datos"`
- **THEN** the system SHALL create a ComentarioTarea linked to the task
- **AND** `autor_id` SHALL be the PROFESOR's user ID
- **AND** respond 201 with the created comment

#### Scenario: Agregar comentario en tarea resuelta
- **WHEN** a user sends POST /api/tareas/<id>/comentarios on a Resuelta task
- **THEN** the system SHALL still create the comment (comments are allowed in any estado)

#### Scenario: PROFESOR comenta tarea ajena
- **WHEN** a PROFESOR tries to comment on a task not assigned to them
- **THEN** the system SHALL respond 403 Forbidden

#### Scenario: Comentario vacío
- **WHEN** POST /api/tareas/<id>/comentarios with `texto: ""`
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Comentario excede máximo
- **WHEN** POST with `texto` exceeding 5000 characters
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Comentar tarea inexistente
- **WHEN** POST /api/tareas/<non-existent-id>/comentarios
- **THEN** the system SHALL respond 404 Not Found

### Requirement: Actualizar descripción de tarea

The system SHALL allow COORDINADOR and ADMIN to update the description of an existing Tarea.

- Method: PATCH
- Path: `/api/tareas/{tarea_id}`
- Guard: `require_permission("tareas:gestionar")`
- Request body: `TareaUpdateRequest` with `descripcion` (str?, optional, max 2000)
- Response 200: `TareaResponse` with updated descripcion
- Only COORDINADOR and ADMIN SHALL update task descriptions

#### Scenario: COORDINADOR actualiza descripción
- **WHEN** a COORDINADOR sends PATCH /api/tareas/<id> with `descripcion: "Descripción actualizada"`
- **THEN** the task descripcion SHALL be updated
- **AND** respond 200

#### Scenario: PROFESOR intenta actualizar descripción
- **WHEN** a PROFESOR sends PATCH with a new `descripcion`
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Tenant isolation en tareas

The system SHALL enforce tenant isolation on all tareas endpoints. Users from one tenant SHALL NOT access tasks from another tenant.

- Every repository query SHALL filter by `tenant_id` from the authenticated session
- Cross-tenant access attempts SHALL return 404 (not 403, to avoid leaking existence)

#### Scenario: Tarea de otro tenant no visible
- **WHEN** a user from tenant A tries to GET /api/tareas/<id> for a task belonging to tenant B
- **THEN** the system SHALL respond 404 Not Found
