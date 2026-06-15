## ADDED Requirements

### Requirement: GET /api/asignaciones — list asignaciones

The system SHALL provide a paginated list endpoint for Asignaciones.

- Method: GET
- Path: `/api/asignaciones`
- Guard: `require_permission("equipos:asignar")`
- Query params: `offset` (int, default 0), `limit` (int, default 20, max 100), `usuario_id` (UUID?, optional filter)
- Response: `{"items": list[AsignacionResponse], "total": int, "offset": int, "limit": int}`
- Each item SHALL include the derived `estado_vigencia` field

#### Scenario: List asignaciones returns paginated responses
- **WHEN** calling GET /api/asignaciones with a valid token having equipos:asignar
- **THEN** a paginated response SHALL be returned with AsignacionResponse items
- **AND** each item SHALL include estado_vigencia

#### Scenario: List asignaciones filter by usuario
- **WHEN** calling GET /api/asignaciones?usuario_id=<uuid>
- **THEN** only Asignaciones for that usuario SHALL be returned

#### Scenario: List asignaciones returns 403 without permission
- **WHEN** calling GET /api/asignaciones without equipos:asignar permission
- **THEN** 403 Forbidden SHALL be returned

### Requirement: POST /api/asignaciones — create asignacion

The system SHALL provide a create endpoint for Asignaciones.

- Method: POST
- Path: `/api/asignaciones`
- Guard: `require_permission("equipos:asignar")`
- Request body: AsignacionCreate (usuario_id, rol_id, materia_id?, carrera_id?, cohorte_id?, comisiones?, responsable_id?, vig_desde, vig_hasta?)
- Response: 201 with AsignacionResponse
- Service layer SHALL enforce non-overlapping vigencia for the same context

#### Scenario: Create asignacion returns 201
- **WHEN** calling POST /api/asignaciones with valid data
- **THEN** 201 Created SHALL be returned with AsignacionResponse

#### Scenario: Create asignacion with overlapping dates returns 409
- **WHEN** calling POST /api/asignaciones with vigencia that overlaps an existing non-deleted assignment for the same context
- **THEN** 409 Conflict SHALL be returned

#### Scenario: Create asignacion references non-existent usuario
- **WHEN** calling POST /api/asignaciones with a non-existent usuario_id
- **THEN** 404 Not Found SHALL be returned

#### Scenario: Create asignacion rejects extra fields
- **WHEN** calling POST /api/asignaciones with unknown fields
- **THEN** 422 validation error SHALL be returned

### Requirement: GET /api/asignaciones/{id} — get asignacion detail

The system SHALL provide a detail endpoint for Asignaciones.

- Method: GET
- Path: `/api/asignaciones/{id}`
- Guard: `require_permission("equipos:asignar")`
- Response: AsignacionResponse with derived estado_vigencia

#### Scenario: Get asignacion by id returns response
- **WHEN** calling GET /api/asignaciones/{id} with an existing id
- **THEN** 200 OK SHALL be returned with AsignacionResponse

#### Scenario: Get asignacion by id returns 404
- **WHEN** calling GET /api/asignaciones/{id} with a non-existent id
- **THEN** 404 Not Found SHALL be returned

### Requirement: PUT /api/asignaciones/{id} — update asignacion

The system SHALL provide an update endpoint for Asignaciones.

- Method: PUT
- Path: `/api/asignaciones/{id}`
- Guard: `require_permission("equipos:asignar")`
- Request body: AsignacionUpdate (all fields optional)
- Response: AsignacionResponse with updated values and derived estado_vigencia

### Requirement: DELETE /api/asignaciones/{id} — soft delete asignacion

The system SHALL provide a soft delete endpoint for Asignaciones.

- Method: DELETE
- Path: `/api/asignaciones/{id}`
- Guard: `require_permission("equipos:asignar")`
- Response: 204 No Content
- The deletion SHALL be soft (deleted_at set, not hard delete)

#### Scenario: Soft delete asignacion returns 204
- **WHEN** calling DELETE /api/asignaciones/{id} with an existing id
- **THEN** 204 No Content SHALL be returned
- **AND** the Asignacion SHALL have deleted_at set

#### Scenario: Soft deleted asignacion excluded from list
- **WHEN** calling GET /api/asignaciones after soft-deleting an asignacion
- **THEN** the deleted asignacion SHALL NOT appear in results
