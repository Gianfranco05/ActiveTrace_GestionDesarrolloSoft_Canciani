## ADDED Requirements

### Requirement: SalarioBase ORM model with temporal validity

The system SHALL persist a `SalarioBase` entity per rol (PROFESOR, TUTOR, NEXO, COORDINADOR) with a fixed monthly `monto`, a `vig_desde` date, and an optional `vig_hasta` date. The combination `(tenant_id, rol)` SHALL be unique: at most one SalarioBase entry exists per rol per tenant at any point in time.

#### Scenario: Create base salary for a rol
- **WHEN** FINANZAS creates a SalarioBase for rol=PROFESOR with monto=50000, vig_desde=2026-03-01
- **THEN** the system persists the record and returns it with a generated UUID

#### Scenario: Query base salary active in a period
- **WHEN** the system queries SalarioBase for rol=PROFESOR and mes=2026-05
- **THEN** the system SHALL return the entry where `vig_desde <= 2026-05-01 AND (vig_hasta IS NULL OR vig_hasta >= 2026-05-31)`

#### Scenario: Base salary with open-ended validity
- **WHEN** a SalarioBase has vig_desde=2026-01-01 and vig_hasta=NULL
- **THEN** the entry is considered valid for any period on or after 2026-01-01

#### Scenario: Duplicate rol rejected
- **WHEN** FINANZAS attempts to create a second SalarioBase for rol=PROFESOR in the same tenant
- **THEN** the system SHALL reject with a 409 Conflict indicating the rol already has a base salary entry

### Requirement: SalarioBase soft delete

The system SHALL support soft-deleting SalarioBase entries. Deleted entries SHALL NOT be considered in temporal validity queries.

#### Scenario: Soft delete removes from active queries
- **WHEN** a SalarioBase entry is soft-deleted (deleted_at set)
- **THEN** subsequent temporal validity queries SHALL NOT return that entry
