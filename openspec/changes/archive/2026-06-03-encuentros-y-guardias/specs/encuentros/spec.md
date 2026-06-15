## ADDED Requirements

### Requirement: Crear slot de encuentro recurrente (F6.1, RN-13 modo 1)

The system SHALL allow PROFESOR and COORDINADOR to create a SlotEncuentro with weekly recurrence. The system MUST automatically generate all InstanciaEncuentro records based on the slot configuration.

- Method: POST
- Path: `/api/encuentros/slots`
- Guard: `require_permission("encuentros:gestionar")`
- Request body: `SlotRecurrenteCreateRequest` with `materia_id` (UUID, required), `asignacion_id` (UUID, required — the creator's assignment), `titulo` (str, required, max 200), `hora` (time, required), `dia_semana` (enum: Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo, required), `fecha_inicio` (date, required), `cant_semanas` (int, required, min 1, max 52), `meet_url` (str?, optional)
- Response 201: `SlotEncuentroResponse` with `id`, `materia_id`, `asignacion_id`, `titulo`, `hora`, `dia_semana`, `fecha_inicio`, `cant_semanas`, `meet_url`, `instancias` (list[InstanciaEncuentroResponse])
- The system SHALL calculate instance dates: first instance on or after `fecha_inicio` that matches `dia_semana`, then weekly for `cant_semanas` weeks
- The system SHALL create all instances in a single transaction with estado "Programado"
- The system SHALL audit the operation with `ENCUENTRO_CREAR`
- PROFESOR scope SHALL be limited to their own Asignacion records

#### Scenario: Crear slot recurrente genera N instancias
- **WHEN** a PROFESOR sends POST /api/encuentros/slots with `dia_semana: Lunes`, `fecha_inicio: 2026-06-08` (Monday), `cant_semanas: 4`
- **THEN** the system SHALL create 1 SlotEncuentro and 4 InstanciaEncuentro records
- **AND** the instance dates SHALL be 2026-06-08, 2026-06-15, 2026-06-22, 2026-06-29
- **AND** all instances SHALL have estado "Programado"

#### Scenario: Fecha de inicio no coincide con día de semana
- **WHEN** a PROFESOR sends POST with `dia_semana: Viernes`, `fecha_inicio: 2026-06-08` (Monday)
- **THEN** the first instance SHALL be 2026-06-12 (next Friday after June 8)
- **AND** subsequent instances SHALL be weekly from that first Friday

#### Scenario: cant_semanas excede el máximo
- **WHEN** a PROFESOR sends POST with `cant_semanas: 53`
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Slot recurrente sin permisos
- **WHEN** a user without `encuentros:gestionar` sends POST /api/encuentros/slots
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Crear encuentro único (F6.2, RN-13 modo 2)

The system SHALL allow creating a single InstanciaEncuentro without a parent SlotEncuentro.

- Method: POST
- Path: `/api/encuentros/instancias`
- Guard: `require_permission("encuentros:gestionar")`
- Request body: `InstanciaUnicaCreateRequest` with `materia_id` (UUID, required), `asignacion_id` (UUID, required), `titulo` (str, required, max 200), `fecha` (date, required), `hora` (time, required), `meet_url` (str?, optional)
- Response 201: `InstanciaEncuentroResponse` with `id`, `materia_id`, `slot_id` (null), `fecha`, `hora`, `titulo`, `estado`, `meet_url`
- The instance estado SHALL default to "Programado"
- The system SHALL audit with `ENCUENTRO_CREAR`

#### Scenario: Crear encuentro único exitoso
- **WHEN** a PROFESOR sends POST /api/encuentros/instancias with valid data
- **THEN** the system SHALL create 1 InstanciaEncuentro with slot_id=null and estado="Programado"
- **AND** respond 201 with the created instance

#### Scenario: Encuentro único con fecha pasada
- **WHEN** a PROFESOR sends POST with fecha in the past
- **THEN** the system SHALL still create the instance (no date validation in creation)

#### Scenario: Encuentro único sin permisos
- **WHEN** a user without `encuentros:gestionar` sends POST /api/encuentros/instancias
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Listar slots de encuentro por materia (F6.5)

The system SHALL provide an endpoint to list SlotEncuentro records for a given materia, with optional filtering by cohorte.

- Method: GET
- Path: `/api/encuentros/slots`
- Guard: `require_permission("encuentros:gestionar")`
- Query params: `materia_id` (UUID?, optional filter), `cohorte_id` (UUID?, optional filter), `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[SlotEncuentroResponse], "total": int, "offset": int, "limit": int}`
- Each SlotEncuentroResponse SHALL include associated InstanciaEncuentro records as nested `instancias`
- PROFESOR SHALL only see slots from their own Asignaciones; COORDINADOR/ADMIN SHALL see all slots in the tenant

#### Scenario: Listar slots de una materia
- **WHEN** a COORDINADOR calls GET /api/encuentros/slots?materia_id=<uuid>
- **THEN** the system SHALL return all slots for that materia with their instances

#### Scenario: PROFESOR solo ve sus slots
- **WHEN** a PROFESOR calls GET /api/encuentros/slots
- **THEN** the system SHALL only return slots where `asignacion_id` belongs to the authenticated user

#### Scenario: Listar slots devuelve vacío
- **WHEN** a materia has no slots and GET /api/encuentros/slots?materia_id=<uuid> is called
- **THEN** the system SHALL return an empty items list with total=0

### Requirement: Listar instancias de encuentro (F6.5)

The system SHALL provide an endpoint to list InstanciaEncuentro records with filters.

- Method: GET
- Path: `/api/encuentros/instancias`
- Guard: `require_permission("encuentros:gestionar")`
- Query params: `materia_id` (UUID?, optional), `slot_id` (UUID?, optional), `estado` (str?, optional: Programado, Realizado, Cancelado), `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[InstanciaEncuentroResponse], "total": int, "offset": int, "limit": int}`
- PROFESOR scope SHALL be limited to instancias from slots they created or instancias independientes with their asignacion_id

#### Scenario: Listar instancias filtradas por estado
- **WHEN** calling GET /api/encuentros/instancias?materia_id=<uuid>&estado=Realizado
- **THEN** the system SHALL return only instances with estado "Realizado"

#### Scenario: Listar instancias con tenant isolation
- **WHEN** two tenants have instances for different materias
- **THEN** each tenant's users SHALL only see their own instances

### Requirement: Editar instancia de encuentro (F6.3, RN-14)

The system SHALL allow editing specific fields of an InstanciaEncuentro: estado, meet_url, video_url, and comentario.

- Method: PATCH
- Path: `/api/encuentros/instancias/{instancia_id}`
- Guard: `require_permission("encuentros:gestionar")`
- Request body: `InstanciaUpdateRequest` with `estado` (enum?, optional: Programado, Realizado, Cancelado), `meet_url` (str?, optional), `video_url` (str?, optional), `comentario` (str?, optional)
- Response 200: `InstanciaEncuentroResponse` with updated fields
- Only the fields present in the request SHALL be updated (partial update)
- Estado changes SHALL be audited with `ENCUENTRO_EDITAR`
- The update SHALL NOT affect the parent slot or other instances (RN-14)
- PROFESOR SHALL only edit instancias from their own slots/assignments

#### Scenario: Marcar instancia como realizada con video
- **WHEN** a PROFESOR sends PATCH /api/encuentros/instancias/<id> with `estado: Realizado` and `video_url: https://...`
- **THEN** the instance estado SHALL change to "Realizado" and video_url SHALL be set
- **AND** other instances from the same slot SHALL remain unchanged (RN-14)

#### Scenario: Cancelar instancia con comentario
- **WHEN** a PROFESOR sends PATCH with `estado: Cancelado` and `comentario: Feriado nacional`
- **THEN** the instance estado SHALL change to "Cancelado" and comentario SHALL be set

#### Scenario: Editar instancia no encontrada
- **WHEN** a PROFESOR sends PATCH with a non-existent instancia_id
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Editar instancia de otro profesor
- **WHEN** a PROFESOR tries to PATCH an instance created by a different PROFESOR
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Generar bloque HTML para aula virtual (F6.4)

The system SHALL generate an HTML block with the calendar of encounters and their recordings for a given slot.

- Method: GET
- Path: `/api/encuentros/slots/{slot_id}/html`
- Guard: `require_permission("encuentros:gestionar")`
- Response 200: `{"html": str}` where `html` is a valid HTML fragment
- The HTML SHALL include: slot title, a list of instances with fecha, hora, estado, meet_url (if any), and video_url (if any)
- Instances with estado "Cancelado" SHALL be visually marked as cancelled
- Instances with estado "Realizado" and video_url SHALL include an embedded link to the recording
- The HTML SHALL be safe for embedding in LMS (no external CSS dependencies, inline styles only)

#### Scenario: Generar HTML con instancias realizadas y programadas
- **WHEN** calling GET /api/encuentros/slots/<id>/html for a slot with 2 Programado and 2 Realizado instances
- **THEN** the system SHALL return an HTML string containing all 4 instances
- **AND** Realizado instances SHALL show their video_url as links
- **AND** Programado instances SHALL show their meet_url

#### Scenario: Generar HTML para slot sin instancias
- **WHEN** calling GET /api/encuentros/slots/<id>/html for a slot with no instances
- **THEN** the system SHALL return an HTML string with the slot title and a message indicating no encounters

#### Scenario: Generar HTML con instancias canceladas
- **WHEN** a slot has a Canceled instance
- **THEN** the HTML SHALL include the instance marked as "Cancelado" without active meet_url

### Requirement: Eliminar slot de encuentro (soft delete)

The system SHALL allow soft-deleting a SlotEncuentro. The associated InstanciaEncuentro records SHALL NOT be deleted.

- Method: DELETE
- Path: `/api/encuentros/slots/{slot_id}`
- Guard: `require_permission("encuentros:gestionar")`
- Response 204: No Content
- The slot SHALL be soft-deleted (deleted_at timestamp set)
- Instances SHALL remain accessible independently

#### Scenario: Eliminar slot no elimina instancias
- **WHEN** a COORDINADOR sends DELETE /api/encuentros/slots/<id> for a slot with 3 instances
- **THEN** the slot SHALL be soft-deleted (deleted_at set)
- **AND** GET /api/encuentros/instancias?slot_id=<id> SHALL still return the 3 instances

#### Scenario: Eliminar slot inexistente
- **WHEN** DELETE is called with a non-existent slot_id
- **THEN** the system SHALL respond 404 Not Found
