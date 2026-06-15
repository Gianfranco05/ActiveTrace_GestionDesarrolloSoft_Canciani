## ADDED Requirements

### Requirement: POST /api/coloquios/{id}/reservas — reservar turno en evaluación (FL-07)

The system SHALL allow an ALUMNO to reserve a time slot in an evaluation they have been convoked to, provided the selected day has available capacity.

- Method: POST
- Path: `/api/coloquios/{id}/reservas`
- Guard: `require_permission("coloquios:reservar")`
- Request body: ReservaRequest
  - `fecha_hora` (datetime, required)
  - `model_config = ConfigDict(extra='forbid')`
- Response: 201 Created with ReservaResponse
- The alumno SHALL be resolved from the authenticated session (JWT), never from a parameter
- The endpoint SHALL validate:
  1. The evaluation exists and is active (activa=True)
  2. The alumno is in alumnos_convocados of the evaluation
  3. The fecha_hora date is present in cupos_por_dia
  4. The count of active reservations for that day is less than the day's cupo
  5. The alumno does not already have an active reservation for the same evaluation
- The endpoint SHALL create a ReservaEvaluacion with estado="Activa"
- The endpoint SHALL generate audit `COLOQUIO_RESERVAR`

#### Scenario: Reservar turno exitoso
- **WHEN** a convoked alumno calls POST /api/coloquios/{id}/reservas with a valid fecha_hora
- **AND** the day has available capacity
- **THEN** 201 Created SHALL be returned with the ReservaResponse (estado="Activa")

#### Scenario: Reservar rechaza alumno no convocado
- **WHEN** an alumno not in alumnos_convocados calls POST /api/coloquios/{id}/reservas
- **THEN** 403 Forbidden SHALL be returned with message "Alumno no convocado"

#### Scenario: Reservar rechaza fecha no disponible
- **WHEN** calling POST /api/coloquios/{id}/reservas with a fecha_hora whose date is not in cupos_por_dia
- **THEN** 400 Bad Request SHALL be returned

#### Scenario: Reservar rechaza cupo lleno
- **WHEN** calling POST /api/coloquios/{id}/reservas on a day where active reservations equal cupo
- **THEN** 409 Conflict SHALL be returned with message "Cupo lleno"

#### Scenario: Reservar rechaza reserva duplicada
- **WHEN** an alumno with an existing active reservation for the same evaluation calls POST /api/coloquios/{id}/reservas again
- **THEN** 409 Conflict SHALL be returned

#### Scenario: Reservar rechaza evaluación inactiva
- **WHEN** calling POST /api/coloquios/{id}/reservas on an evaluation with activa=False
- **THEN** 400 Bad Request SHALL be returned

#### Scenario: Reservar genera auditoría
- **WHEN** a reservation is created successfully
- **THEN** an AuditLog entry with action "COLOQUIO_RESERVAR" SHALL be created

### Requirement: PATCH /api/coloquios/reservas/{id}/cancelar — cancelar reserva (FL-07)

The system SHALL allow an ALUMNO to cancel their own active reservation, freeing the slot for other students.

- Method: PATCH
- Path: `/api/coloquios/reservas/{id}/cancelar`
- Guard: `require_permission("coloquios:reservar")`
- Response: ReservaResponse with estado="Cancelada"
- The alumno SHALL only cancel their own reservations (validated against session user_id)
- The endpoint SHALL validate the reservation exists and is in estado="Activa"
- The endpoint SHALL generate audit `COLOQUIO_CANCELAR`

#### Scenario: Cancelar reserva propia exitoso
- **WHEN** an alumno calls PATCH /api/coloquios/reservas/{id}/cancelar on their own active reservation
- **THEN** the reservation's estado SHALL change to "Cancelada"

#### Scenario: Cancelar reserva ajena rechazado
- **WHEN** an alumno calls PATCH /api/coloquios/reservas/{id}/cancelar on another alumno's reservation
- **THEN** 403 Forbidden SHALL be returned

#### Scenario: Cancelar reserva ya cancelada
- **WHEN** calling PATCH /api/coloquios/reservas/{id}/cancelar on an already cancelled reservation
- **THEN** 409 Conflict SHALL be returned

#### Scenario: Cancelar reserva inexistente
- **WHEN** calling PATCH /api/coloquios/reservas/{id}/cancelar with a non-existent id
- **THEN** 404 Not Found SHALL be returned

#### Scenario: Cancelar genera auditoría
- **WHEN** a reservation is cancelled successfully
- **THEN** an AuditLog entry with action "COLOQUIO_CANCELAR" SHALL be created

### Requirement: GET /api/coloquios/mis-reservas — mis reservas del alumno autenticado (FL-07)

The system SHALL provide an endpoint for authenticated users to view their own reservations across all evaluations.

- Method: GET
- Path: `/api/coloquios/mis-reservas`
- Guard: `require_authenticated` (any authenticated role)
- Query params: `estado` (str?, "Activa"|"Cancelada" — default "Activa"), `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[ReservaResponse], "total": int, "offset": int, "limit": int}`
- The alumno SHALL be resolved from the authenticated session
- Each item SHALL include evaluacion_id, fecha_hora, estado

#### Scenario: Mis reservas activas
- **WHEN** an authenticated alumno with active reservations calls GET /api/coloquios/mis-reservas
- **THEN** a paginated list of their active reservations SHALL be returned

#### Scenario: Mis reservas vacío
- **WHEN** an authenticated user with no reservations calls GET /api/coloquios/mis-reservas
- **THEN** an empty list SHALL be returned

#### Scenario: Mis reservas filtradas por estado
- **WHEN** calling GET /api/coloquios/mis-reservas?estado=Cancelada
- **THEN** only cancelled reservations for the authenticated user SHALL be returned

### Requirement: GET /api/coloquios/admin/agenda — agenda global de reservas (F7.5)

The system SHALL provide COORDINADOR/ADMIN with a global view of all active reservations across all evaluations.

- Method: GET
- Path: `/api/coloquios/admin/agenda`
- Guard: `require_permission("coloquios:gestionar")`
- Query params: `materia_id` (UUID?, filter), `evaluacion_id` (UUID?, filter), `fecha_desde` (date?, filter), `fecha_hasta` (date?, filter), `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[ReservaAgendaResponse], "total": int, "offset": int, "limit": int}`
- Results SHALL include materia_nombre, cohorte_nombre, instancia, alumno_nombre, alumno_apellidos
- Results SHALL be ordered by fecha_hora ascending

#### Scenario: Agenda con filtro por materia
- **WHEN** calling GET /api/coloquios/admin/agenda?materia_id=<uuid>
- **THEN** only reservations for evaluations of that materia SHALL be returned

#### Scenario: Agenda con filtro por rango de fechas
- **WHEN** calling GET /api/coloquios/admin/agenda?fecha_desde=2026-06-01&fecha_hasta=2026-06-30
- **THEN** only reservations within that date range SHALL be returned

#### Scenario: Agenda vacía sin reservas
- **WHEN** calling GET /api/coloquios/admin/agenda with no reservations in the tenant
- **THEN** an empty list SHALL be returned
