## ADDED Requirements

### Requirement: POST /api/equipos/masiva — asignación masiva de docentes (F4.4)

The system SHALL provide an endpoint to bulk-create Asignaciones for multiple usuarios with the same academic context (materia, carrera, cohorte), rol, and vigencia.

- Method: POST
- Path: `/api/equipos/masiva`
- Guard: `require_permission("equipos:asignar")`
- Request body: AsignacionMasivaRequest
  - `materia_id` (UUID, required)
  - `carrera_id` (UUID, required)
  - `cohorte_id` (UUID, required)
  - `rol_id` (UUID, required)
  - `usuario_ids` (list[UUID], required — min 1, max 100)
  - `vig_desde` (date, required)
  - `vig_hasta` (date?, optional)
  - `comisiones` (str?, optional)
  - `model_config = ConfigDict(extra='forbid')`
- Response: 201 Created with `{"items": list[AsignacionResponse], "total": int}`
- The operation SHALL be transactional — ALL Asignaciones are created or NONE (rollback on any failure)
- Each Asignacion SHALL be created with:
  - usuario_id from the list, rol_id, materia_id, carrera_id, cohorte_id, comisiones as provided
  - vig_desde, vig_hasta as provided
  - responsable_id = None (the coordinator must set hierarchy manually after bulk creation)
  - tenant_id from the authenticated user's session
- The endpoint SHALL validate that ALL usuario_ids exist before creating any Asignacion
- The endpoint SHALL generate audit `ASIGNACION_MODIFICAR` with filas_afectadas = len(usuario_ids)

#### Scenario: Asignacion masiva creates N asignaciones
- **WHEN** calling POST /api/equipos/masiva with 3 valid usuario_ids
- **THEN** 201 Created SHALL be returned with 3 AsignacionResponse items
- **AND** each Asignacion SHALL have the same materia_id, carrera_id, cohorte_id, rol_id, vig_desde, vig_hasta

#### Scenario: Asignacion masiva rolls back on non-existent usuario
- **WHEN** calling POST /api/equipos/masiva with a non-existent usuario_id in the list
- **THEN** 404 Not Found SHALL be returned
- **AND** no Asignaciones SHALL be created (full rollback)

#### Scenario: Asignacion masiva enforces unique constraint
- **WHEN** calling POST /api/equipos/masiva and one of the combinations violates the unique constraint
- **THEN** 409 Conflict SHALL be returned
- **AND** no Asignaciones SHALL be created (full rollback)

#### Scenario: Asignacion masiva rejects more than 100 usuarios
- **WHEN** calling POST /api/equipos/masiva with 101 usuario_ids
- **THEN** 422 validation error SHALL be returned

#### Scenario: Asignacion masiva rejects extra fields
- **WHEN** calling POST /api/equipos/masiva with unknown fields
- **THEN** 422 validation error SHALL be returned

#### Scenario: Asignacion masiva generates audit
- **WHEN** calling POST /api/equipos/masiva successfully
- **THEN** an AuditLog entry with action "ASIGNACION_MODIFICAR" SHALL be created
- **AND** filas_afectadas SHALL equal the number of created Asignaciones
