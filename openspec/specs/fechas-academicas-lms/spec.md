# fechas-academicas-lms Specification

## Purpose
Generar un fragmento HTML con el cronograma de fechas académicas listo para publicar en el aula virtual del LMS.

## ADDED Requirements

### Requirement: Generar fragmento HTML para aula virtual (F5.4)

The system SHALL generate an HTML fragment containing the calendar of academic dates for a given materia × cohorte, formatted for embedding in an LMS virtual classroom.

- Method: GET
- Path: `/api/fechas-academicas/lms/html`
- Guard: `require_permission("estructura:gestionar")`
- Query params: `materia_id` (UUID, required), `cohorte_id` (UUID, required)
- Response 200: `{"html": str}` where `html` is a valid HTML fragment
- The HTML SHALL include: a title with the materia name, a table with columns Fecha, Tipo, N° Instancia, Título
- Rows SHALL be ordered by fecha ASC
- Soft-deleted records SHALL be excluded
- The HTML SHALL use inline styles only (no external CSS) for LMS compatibility
- The system SHALL return 404 if materia_id or cohorte_id do not exist or do not belong to the tenant

#### Scenario: Generar HTML con fechas programadas
- **WHEN** calling GET /api/fechas-academicas/lms/html?materia_id=<uuid>&cohorte_id=<uuid> for a materia with 3 fechas
- **THEN** the system SHALL return an HTML string containing a table with 3 rows
- **AND** the table SHALL have columns: Fecha, Tipo, N° Instancia, Título
- **AND** rows SHALL be ordered by fecha ASC

#### Scenario: Generar HTML con diferentes tipos de evaluación
- **WHEN** a materia has 1 Parcial, 1 TP, and 1 Coloquio
- **THEN** the HTML table SHALL show each type as a separate row with its corresponding numero and titulo

#### Scenario: Generar HTML sin fechas
- **WHEN** a materia × cohorte has no FechaAcademica records
- **THEN** the system SHALL return an HTML string with the materia title and a message indicating no evaluation dates are scheduled yet

#### Scenario: Generar HTML con materia inexistente
- **WHEN** GET /api/fechas-academicas/lms/html is called with a non-existent materia_id
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Generar HTML sin permisos
- **WHEN** a user without `estructura:gestionar` calls GET /api/fechas-academicas/lms/html
- **THEN** the system SHALL respond 403 Forbidden

#### Scenario: Generar HTML con fechas soft-deleted excluidas
- **WHEN** a materia × cohorte has 2 active fechas and 1 soft-deleted fecha
- **THEN** the HTML table SHALL show only the 2 active fechas

#### Scenario: HTML usa inline styles sin dependencias externas
- **WHEN** the HTML fragment is generated
- **THEN** it SHALL NOT contain any `<link>` tags or references to external stylesheets
- **AND** all styling SHALL be applied via inline `style` attributes on elements
