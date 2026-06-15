## ADDED Requirements

### Requirement: File parser for .xlsx and .csv

The system SHALL provide a FileParser service that parses student roster files in .xlsx (Excel) and .csv formats into structured rows. The parser SHALL auto-detect column mappings by normalizing header names.

**Column mapping rules:**

| Input header (case-insensitive, normalized) | Field |
|---------------------------------------------|-------|
| `nombre`, `name`, `nombres`, `alumno` | `nombre` |
| `apellido`, `apellidos`, `apellido(s)`, `surname`, `apellido/s` | `apellidos` |
| `email`, `e-mail`, `correo`, `mail`, `correo electrónico` | `email` |
| `comision`, `comisión`, `com`, `section`, `comisión/grupo`, `grupo`, `division` | `comision` |
| `regional`, `sede`, `delegacion`, `delegación`, `sede/regional` | `regional` |

#### Scenario: Parse valid xlsx file
- **GIVEN** a valid .xlsx file with headers `nombre`, `apellidos`, `email`, `comision`, `regional` and 50 data rows
- **WHEN** calling FileParser.parse()
- **THEN** it SHALL return a ParseResult with total_rows=50, 50 parsed rows, auto-detected column mapping

#### Scenario: Parse csv file
- **GIVEN** a valid .csv file with headers `nombre`, `apellidos`, `email`
- **WHEN** calling FileParser.parse()
- **THEN** it SHALL return a ParseResult with correctly parsed rows and auto-detected mapping

#### Scenario: Parse with missing optional columns
- **GIVEN** a file with only `nombre`, `apellidos`, `email` headers
- **WHEN** calling FileParser.parse()
- **THEN** comision and regional SHALL be None for all rows

#### Scenario: Parse with alternate headers
- **GIVEN** a file with headers `NOMBRE`, `APELLIDO(S)`, `CORREO`, `GRUPO`
- **WHEN** calling FileParser.parse()
- **THEN** the detected mapping SHALL be `{nombre: nombre, apellidos: apellidos, email: correo, comision: grupo}`

#### Scenario: Parse fails for unsupported format
- **GIVEN** a file with .pdf extension
- **WHEN** calling FileParser.parse()
- **THEN** a `ValueError` SHALL be raised with message "Unsupported file format"

#### Scenario: Parse handles empty file
- **GIVEN** a .csv file with only headers and no data rows
- **WHEN** calling FileParser.parse()
- **THEN** it SHALL return total_rows=0, empty rows list

#### Scenario: Parse handles rows with missing required fields
- **GIVEN** a .csv file where some rows are missing `nombre` or `apellidos`
- **WHEN** calling FileParser.parse()
- **THEN** rows with empty nombre/apellidos SHALL be collected in `errors` and skipped from `rows`

### Requirement: Two-phase import flow (preview → confirm)

The system SHALL implement a two-phase import flow: Phase 1 parses the file and returns a preview WITHOUT persisting anything; Phase 2 confirms the import and creates VersionPadron + EntradaPadron rows.

#### Scenario: Preview returns sample rows
- **GIVEN** a valid file with 200 rows
- **WHEN** calling PadronService.preview(file_content, filename) with default preview_limit=20
- **THEN** the response SHALL contain: filename, total_rows=200, preview_rows with 20 entries, detected_columns mapping

#### Scenario: Confirm import creates version and entries
- **GIVEN** a valid parse result and (materia_id, cohorte_id, cargado_por)
- **WHEN** calling PadronService.confirm_import() with the parsed data
- **THEN** a new VersionPadron SHALL be created with activa=True
- **AND** EntradaPadron rows SHALL be created for all parsed rows
- **AND** the previous active version (if any) SHALL be deactivated

#### Scenario: Confirm import with column mapping override
- **GIVEN** a parsed file where auto-detection mapped incorrectly
- **WHEN** calling PadronService.confirm_import() with a custom column_mapping override
- **THEN** the entries SHALL use the overridden column mapping

#### Scenario: Confirm import audits the action
- **GIVEN** a successful import of 50 rows
- **WHEN** calling PadronService.confirm_import()
- **THEN** AuditService.log() SHALL be called with accion="PADRON_CARGAR", filas_afectadas=50, materia_id, and cargado_por as actor_id

### Requirement: Vaciar entries (F1.5, RN-04)

The system SHALL allow soft-deleting all EntradaPadron entries for a given VersionPadron, but ONLY if the version is NOT the active one (prevents accidental data loss).

#### Scenario: Vaciar entries for non-active version
- **GIVEN** a VersionPadron with activa=False and 30 EntradaPadron entries
- **WHEN** calling PadronService.vaciar_version(version_id)
- **THEN** all 30 entries SHALL have deleted_at set
- **AND** AuditService.log() SHALL be called with accion="PADRON_CARGAR", filas_afectadas=30
- **AND** the response SHALL include entries_vaciadas=30

#### Scenario: Vaciar fails for active version
- **GIVEN** a VersionPadron with activa=True
- **WHEN** calling PadronService.vaciar_version(version_id)
- **THEN** a ValidationError SHALL be raised with message "Cannot vaciar active version"
- **AND** no entries SHALL be deleted

#### Scenario: Vaciar non-existent version
- **WHEN** calling PadronService.vaciar_version with a non-existent UUID
- **THEN** a NotFoundError SHALL be raised
