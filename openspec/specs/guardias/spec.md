# guardias Specification

## Purpose
TBD - created by archiving change encuentros-y-guardias. Update Purpose after archive.
## Requirements
### Requirement: Registrar guardia (F6.6)

The system SHALL allow TUTOR, COORDINADOR, and ADMIN to register a Guardia record documenting attention provided to students.

- Method: POST
- Path: `/api/guardias`
- Guard: `require_permission("encuentros:gestionar")`
- Request body: `GuardiaCreateRequest` with `asignacion_id` (UUID, required — the guard's assignment), `materia_id` (UUID, required), `carrera_id` (UUID, required), `cohorte_id` (UUID, required), `dia` (enum, required: Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo), `horario` (str, required, max 50, eg "14:00–14:45"), `comentarios` (str?, optional)
- Response 201: `GuardiaResponse` with `id`, `asignacion_id`, `materia_id`, `carrera_id`, `cohorte_id`, `dia`, `horario`, `estado` (default "Pendiente"), `comentarios`, `creada_at`
- The system SHALL audit the operation with `GUARDIA_REGISTRAR`
- TUTOR scope SHALL be limited to their own Asignacion records (only register their own guardias)

#### Scenario: TUTOR registra su guardia exitosamente
- **WHEN** a TUTOR sends POST /api/guardias with valid data for their own asignacion
- **THEN** the system SHALL create a Guardia with estado="Pendiente"
- **AND** respond 201 with the created guardia

#### Scenario: Registrar guardia sin permisos
- **WHEN** an ALUMNO sends POST /api/guardias
- **THEN** the system SHALL respond 403 Forbidden

#### Scenario: Registrar guardia con campos requeridos faltantes
- **WHEN** POST /api/guardias omits `materia_id`
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Registrar guardia con asignacion que no es propia (TUTOR)
- **WHEN** a TUTOR tries to register a guardia with an asignacion_id belonging to another user
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Editar guardia

The system SHALL allow updating estado and comentarios of an existing Guardia.

- Method: PATCH
- Path: `/api/guardias/{guardia_id}`
- Guard: `require_permission("encuentros:gestionar")`
- Request body: `GuardiaUpdateRequest` with `estado` (enum?, optional: Pendiente, Realizada, Cancelada), `comentarios` (str?, optional)
- Response 200: `GuardiaResponse` with updated fields
- Only provided fields SHALL be updated (partial update)
- TUTOR SHALL only edit their own guardias

#### Scenario: Marcar guardia como realizada
- **WHEN** a TUTOR sends PATCH /api/guardias/<id> with `estado: Realizada`
- **THEN** the guardia estado SHALL change to "Realizada"

#### Scenario: Editar guardia que no es propia
- **WHEN** a TUTOR tries to PATCH a guardia created by another user
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Consultar guardias (F6.6)

The system SHALL provide an endpoint for COORDINADOR and ADMIN to query all guardias in the tenant with filters.

- Method: GET
- Path: `/api/guardias`
- Guard: `require_permission("encuentros:gestionar")`
- Query params: `materia_id` (UUID?, optional), `carrera_id` (UUID?, optional), `cohorte_id` (UUID?, optional), `dia` (enum?, optional), `estado` (enum?, optional: Pendiente, Realizada, Cancelada), `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[GuardiaResponse], "total": int, "offset": int, "limit": int}`
- COORDINADOR/ADMIN SHALL see all guardias in the tenant
- TUTOR SHALL only see their own guardias
- Each GuardiaResponse SHALL include relacion names (materia_nombre, carrera_nombre, cohorte_nombre) resolved via joins

#### Scenario: COORDINADOR consulta todas las guardias del tenant
- **WHEN** a COORDINADOR calls GET /api/guardias
- **THEN** the system SHALL return all guardias in the tenant

#### Scenario: Filtrar guardias por materia y estado
- **WHEN** calling GET /api/guardias?materia_id=<uuid>&estado=Pendiente
- **THEN** the system SHALL return only Pendiente guardias for that materia

#### Scenario: TUTOR consulta solo sus guardias
- **WHEN** a TUTOR calls GET /api/guardias
- **THEN** the system SHALL return only guardias where asignacion_id belongs to the TUTOR

#### Scenario: Consultar guardias sin permisos
- **WHEN** an ALUMNO calls GET /api/guardias
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Exportar guardias (F6.6)

The system SHALL allow COORDINADOR and ADMIN to export guardias as a CSV file.

- Method: GET
- Path: `/api/guardias/export`
- Guard: `require_permission("encuentros:gestionar")`
- Query params: same filters as GET /api/guardias (`materia_id`, `carrera_id`, `cohorte_id`, `dia`, `estado`)
- Response 200: CSV file with headers: id, materia, carrera, cohorte, dia, horario, estado, comentarios, creada_at, tutor
- Content-Type: `text/csv`
- TUTOR scope SHALL also be supported (export their own guardias)

#### Scenario: Exportar guardias como CSV
- **WHEN** a COORDINADOR calls GET /api/guardias/export
- **THEN** the system SHALL return a CSV with header row and all matching guardia rows
- **AND** Content-Type SHALL be text/csv

#### Scenario: Exportar guardias con filtros
- **WHEN** calling GET /api/guardias/export?estado=Realizada
- **THEN** the CSV SHALL contain only Realizada guardias

#### Scenario: Exportar sin datos
- **WHEN** no guardias match the filters
- **THEN** the CSV SHALL contain only the header row

