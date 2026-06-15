## ADDED Requirements

### Requirement: Grade file parser with numeric/textual activity detection

The system SHALL provide a grade file parser that can process .xlsx and .csv files exported from an LMS, detecting which columns represent evaluable activities and classifying them as numeric or textual.

**Column classification rules:**
- **Identifying columns**: `nombre`, `name`, `nombres`, `alumno` → full name; `apellido`, `apellidos`, `surname` → surnames; `email`, `e-mail`, `correo`, `mail` → email; `comision`, `comisión`, `com`, `section` → group; `regional`, `sede`, `delegacion` → regional office. These are NOT activities.
- **Numeric activity columns (RN-01)**: Any column whose header (case-insensitive, trimmed) ends in `(Real)`. The suffix `(Real)` is removed to obtain the activity name.
- **Textual activity columns (RN-02)**: Any non-identifying column that does NOT end in `(Real)`. The full header is the activity name.

#### Scenario: Parse grade file and detect numeric and textual activities
- **GIVEN** a .xlsx grade file with headers: `nombre`, `apellidos`, `email`, `TP1 (Real)`, `TP2 (Real)`, `Participacion`, `Entrega Final`
- **WHEN** parsing the file
- **THEN** detected activities SHALL be:
  - `TP1` → tipo=Numerica
  - `TP2` → tipo=Numerica
  - `Participacion` → tipo=Textual
  - `Entrega Final` → tipo=Textual

#### Scenario: Parse grade file returns total row count
- **GIVEN** a grade file with 48 data rows and a header row
- **WHEN** parsing the file
- **THEN** total_rows SHALL be 48

#### Scenario: Parse grade file with no numeric activities
- **GIVEN** a grade file with only textual activity columns
- **WHEN** parsing the file
- **THEN** all detected activities SHALL have tipo="Textual"

#### Scenario: Parse grade file with no activities (only identifying columns)
- **GIVEN** a grade file with only `nombre`, `apellidos`, `email` columns
- **WHEN** parsing the file
- **THEN** actividades_detectadas SHALL be empty
- **AND** total_rows SHALL be 0 (no data beyond headers)

---

### Requirement: Two-phase import flow (preview → confirm)

The system SHALL implement a two-phase import flow for grades: Phase 1 parses the file and returns a preview with detected activities WITHOUT persisting anything; Phase 2 confirms the import and creates Calificacion records.

#### Scenario: Preview returns detected activities and sample rows
- **GIVEN** a valid grade file with 200 rows and 3 activity columns
- **WHEN** calling preview(file_content, filename) with default preview_limit=20
- **THEN** the response SHALL contain: filename, total_rows=200, preview_rows with 20 entries, actividades_detectadas with 3 entries (each with header, nombre, tipo)

#### Scenario: Preview is idempotent (no side effects)
- **GIVEN** a valid grade file
- **WHEN** calling preview() twice
- **THEN** no Calificacion records SHALL exist in the database after either call

#### Scenario: Confirm import creates calificaciones with derived aprobado
- **GIVEN** a valid parsed file with 10 rows and 3 activity columns
- **AND** an existing UmbralMateria for the materia with umbral_pct=60
- **WHEN** calling confirm_import() with materia_id, cohorte_id, actividad_mapping
- **THEN** 30 Calificacion records SHALL be created (10 rows × 3 activities)
- **AND** each Calificacion's aprobado SHALL be derived correctly per the umbral rules
- **AND** the audit log SHALL record CALIFICACIONES_IMPORTAR with filas_afectadas=30

#### Scenario: Confirm import with actividad_mapping override
- **GIVEN** a parsed file where the user wants to rename an activity
- **WHEN** calling confirm_import() with `actividad_mapping={"TP1 (Real)": "Trabajo Practico 1"}`
- **THEN** the Calificacion records for that column SHALL use "Trabajo Practico 1" as the actividad name

#### Scenario: Confirm import without UmbralMateria uses default 60%
- **GIVEN** a valid parsed file
- **AND** NO UmbralMateria exists for the materia
- **WHEN** calling confirm_import()
- **THEN** numeric grades >= 60 SHALL have aprobado=true
- **AND** numeric grades < 60 SHALL have aprobado=false

#### Scenario: Confirm import audits the action
- **GIVEN** a successful import of 50 calificaciones (10 rows × 5 activities)
- **WHEN** calling confirm_import()
- **THEN** AuditService.log() SHALL be called with accion="CALIFICACIONES_IMPORTAR", filas_afectadas=50, materia_id, and cargado_por as actor_id

#### Scenario: Confirm import respects RN-04 scope isolation
- **GIVEN** two different users (Teacher A and Teacher B) for the same materia
- **WHEN** each imports grades for the same materia
- **THEN** Teacher A's Calificacions SHALL have cargado_por=Teacher_A.id
- **AND** Teacher B's Calificacions SHALL have cargado_por=Teacher_B.id
- **AND** each teacher SHALL only see their own grades when querying without coordinator scope

#### Scenario: Confirm import fails for non-existent materia
- **WHEN** calling confirm_import() with a non-existent materia_id
- **THEN** a validation error SHALL be raised
- **AND** no Calificacion records SHALL be created
