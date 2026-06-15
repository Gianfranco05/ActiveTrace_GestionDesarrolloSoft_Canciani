## ADDED Requirements

### Requirement: CRUD operations for SalarioBase

The system SHALL expose API endpoints to create, read, update, and soft-delete SalarioBase entries. All endpoints SHALL be protected by `liquidaciones:configurar-salarios` for write operations and `liquidaciones:ver` for read operations.

#### Scenario: List all base salaries
- **WHEN** FINANZAS calls GET /api/liquidaciones/salarios/base
- **THEN** the system returns all non-deleted SalarioBase entries for the tenant

#### Scenario: Create base salary
- **WHEN** FINANZAS calls POST /api/liquidaciones/salarios/base with rol=PROFESOR, monto=50000, vig_desde=2026-06-01
- **THEN** the system creates the entry and returns it with a UUID

#### Scenario: Update base salary (new vigencia)
- **WHEN** FINANZAS updates a SalarioBase with new monto=55000 via PUT
- **THEN** the system updates the monto field

#### Scenario: Soft delete base salary
- **WHEN** FINANZAS calls DELETE /api/liquidaciones/salarios/base/{id}
- **THEN** the system sets deleted_at and the entry is excluded from future queries

### Requirement: CRUD operations for SalarioPlus

The system SHALL expose API endpoints to create, read, update, and soft-delete SalarioPlus entries. All endpoints SHALL be protected by `liquidaciones:configurar-salarios` for write operations and `liquidaciones:ver` for read operations.

#### Scenario: List all plus entries
- **WHEN** FINANZAS calls GET /api/liquidaciones/salarios/plus
- **THEN** the system returns all non-deleted SalarioPlus entries for the tenant

#### Scenario: Create plus entry
- **WHEN** FINANZAS calls POST /api/liquidaciones/salarios/plus with grupo=PROG, rol=PROFESOR, monto=5000, vig_desde=2026-06-01
- **THEN** the system creates the entry and returns it with a UUID

#### Scenario: Update plus entry
- **WHEN** FINANZAS updates a SalarioPlus with new monto=6000 via PUT
- **THEN** the system updates the monto field

#### Scenario: Conflict on duplicate grupo-rol
- **WHEN** FINANZAS creates a SalarioPlus with grupo=PROG, rol=PROFESOR and one already exists
- **THEN** the system SHALL reject with 409 Conflict

### Requirement: CRUD operations for GrupoMateria mapping

The system SHALL expose API endpoints to create, read, and delete GrupoMateria mappings. All endpoints SHALL be protected by `liquidaciones:configurar-salarios` for write operations and `liquidaciones:ver` for read operations.

#### Scenario: List grupo-materia mappings
- **WHEN** FINANZAS calls GET /api/liquidaciones/salarios/grupos
- **THEN** the system returns all GrupoMateria entries for the tenant

#### Scenario: Add materia to grupo
- **WHEN** FINANZAS calls POST /api/liquidaciones/salarios/grupos with grupo=PROG, materia_id=MAT-01
- **THEN** the system creates the mapping

#### Scenario: Remove materia from grupo
- **WHEN** FINANZAS calls DELETE /api/liquidaciones/salarios/grupos/{id}
- **THEN** the system deletes the mapping

#### Scenario: Duplicate grupo-materia rejected
- **WHEN** FINANZAS adds materia MAT-01 to grupo PROG and the mapping already exists
- **THEN** the system SHALL reject with 409 Conflict

### Requirement: Permission enforcement on salary grid

The system SHALL enforce `liquidaciones:configurar-salarios` permission on all write endpoints (create, update, delete) for SalarioBase, SalarioPlus, and GrupoMateria. Read endpoints SHALL require `liquidaciones:ver`.

#### Scenario: Unauthorized write attempt
- **WHEN** a user without `liquidaciones:configurar-salarios` attempts to POST a SalarioBase
- **THEN** the system SHALL return 403 Forbidden

#### Scenario: Authorized read
- **WHEN** a user with `liquidaciones:ver` calls GET /api/liquidaciones/salarios/base
- **THEN** the system SHALL return the list
