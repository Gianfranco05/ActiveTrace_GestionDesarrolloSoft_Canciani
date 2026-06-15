## ADDED Requirements

### Requirement: PATCH /api/equipos/vigencia — modificar vigencia general del equipo (F4.6)

The system SHALL provide an endpoint to batch-update the vigencia dates (vig_desde, vig_hasta) for all Asignaciones in a given equipo (materia × carrera × cohorte).

- Method: PATCH
- Path: `/api/equipos/vigencia`
- Guard: `require_permission("equipos:asignar")`
- Query params: `materia_id` (UUID, required), `carrera_id` (UUID, required), `cohorte_id` (UUID, required)
- Request body: VigenciaUpdateRequest
  - `vig_desde` (date, required)
  - `vig_hasta` (date?, optional — None means open-ended)
  - `model_config = ConfigDict(extra='forbid')`
- Response: EquipoDetailResponse with updated Asignaciones
- The operation SHALL validate that vig_desde <= vig_hasta (if vig_hasta is provided)
- The operation SHALL return 404 if the equipo has no Asignaciones
- The operation SHALL generate audit `ASIGNACION_MODIFICAR` with filas_afectadas = count of updated Asignaciones

#### Scenario: Modificar vigencia updates all team assignments
- **WHEN** calling PATCH /api/equipos/vigencia with valid params and body
- **THEN** 200 OK SHALL be returned with updated EquipoDetailResponse
- **AND** all Asignaciones in the equipo SHALL have the new vig_desde and vig_hasta values

#### Scenario: Modificar vigencia validates date range
- **WHEN** calling PATCH /api/equipos/vigencia with vig_desde > vig_hasta
- **THEN** 422 validation error SHALL be returned

#### Scenario: Modificar vigencia returns 404
- **WHEN** calling PATCH /api/equipos/vigencia with a combination that has no Asignaciones
- **THEN** 404 Not Found SHALL be returned

#### Scenario: Modificar vigencia with null vig_hasta opens vigencia
- **WHEN** calling PATCH /api/equipos/vigencia with vig_hasta = None
- **THEN** all Asignaciones in the equipo SHALL have vig_hasta = NULL (open-ended)

#### Scenario: Modificar vigencia updates only the target equipo
- **WHEN** calling PATCH /api/equipos/vigencia for one equipo
- **THEN** Asignaciones in other equipos SHALL NOT be affected

#### Scenario: Modificar vigencia generates audit
- **WHEN** calling PATCH /api/equipos/vigencia successfully
- **THEN** an AuditLog entry with action "ASIGNACION_MODIFICAR" SHALL be created
- **AND** filas_afectadas SHALL equal the number of updated Asignaciones
