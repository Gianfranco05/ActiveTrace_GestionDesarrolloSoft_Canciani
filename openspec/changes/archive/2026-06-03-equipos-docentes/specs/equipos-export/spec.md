## ADDED Requirements

### Requirement: GET /api/equipos/export — exportar equipo docente (F4.7)

The system SHALL provide an endpoint to export all Asignaciones of a given equipo as a downloadable CSV file.

- Method: GET
- Path: `/api/equipos/export`
- Guard: `require_permission("equipos:asignar")`
- Query params: `materia_id` (UUID, required), `carrera_id` (UUID, required), `cohorte_id` (UUID, required)
- Response:
  - Content-Type: `text/csv`
  - Content-Disposition: `attachment; filename="equipo_{materia_nombre}_{carrera_nombre}_{cohorte_nombre}.csv"` (sanitized names)
  - Status: 200 OK
- The CSV SHALL include the following columns:
  - `usuario_id`, `nombre`, `apellidos`, `rol`, `materia`, `carrera`, `cohorte`, `comisiones`, `vig_desde`, `vig_hasta`, `estado_vigencia`
- The CSV SHALL use comma as delimiter and include a header row
- String values containing commas, newlines, or double quotes SHALL be properly quoted per RFC 4180
- The endpoint SHALL return 404 if the equipo has no Asignaciones
- The export SHALL use the native Python `csv` module (stdlib, no external dependencies)
- The endpoint SHALL NOT generate an audit entry (read-only operation)

#### Scenario: Export equipo returns CSV file
- **WHEN** calling GET /api/equipos/export with valid params
- **THEN** 200 OK SHALL be returned with Content-Type: text/csv
- **AND** the response SHALL contain a valid CSV with header row and data rows

#### Scenario: Export CSV includes all assignments
- **WHEN** calling GET /api/equipos/export
- **THEN** the CSV SHALL have one row per Asignacion in the equipo
- **AND** the count of data rows SHALL equal the total Asignaciones in the equipo

#### Scenario: Export CSV columns are correct
- **WHEN** calling GET /api/equipos/export
- **THEN** the CSV SHALL have the columns: usuario_id, nombre, apellidos, rol, materia, carrera, cohorte, comisiones, vig_desde, vig_hasta, estado_vigencia

#### Scenario: Export CSV escapes special characters
- **WHEN** an Asignacion has comisiones containing commas or quotes
- **THEN** the CSV SHALL properly quote those values per RFC 4180

#### Scenario: Export equipo returns 404
- **WHEN** calling GET /api/equipos/export with a combination that has no Asignaciones
- **THEN** 404 Not Found SHALL be returned
