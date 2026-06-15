## ADDED Requirements

### Requirement: SalarioPlus ORM model with (grupo, rol) key

The system SHALL persist a `SalarioPlus` entity identified by the pair `(grupo, rol)`, with a `monto` per comision, a `descripcion`, a `vig_desde` date, and an optional `vig_hasta` date. The combination `(tenant_id, grupo, rol)` SHALL be unique.

#### Scenario: Create plus for a grupo-rol pair
- **WHEN** FINANZAS creates a SalarioPlus for grupo=PROG, rol=PROFESOR with monto=5000, vig_desde=2026-03-01
- **THEN** the system persists the record and returns it with a generated UUID

#### Scenario: Query plus active in a period
- **WHEN** the system queries SalarioPlus for grupo=PROG, rol=PROFESOR and mes=2026-05
- **THEN** the system SHALL return the entry where `vig_desde <= 2026-05-01 AND (vig_hasta IS NULL OR vig_hasta >= 2026-05-31)`

#### Scenario: Duplicate grupo-rol rejected
- **WHEN** FINANZAS attempts to create a second SalarioPlus for grupo=PROG, rol=PROFESOR in the same tenant
- **THEN** the system SHALL reject with a 409 Conflict

### Requirement: SalarioPlus monto is per-comision

The `monto` field in SalarioPlus SHALL represent the amount per individual comision. When a docente has N comisiones in materias of the same grupo, the system SHALL accumulate N × monto.

#### Scenario: Docente with 3 comisiones in same grupo
- **WHEN** a docente has 3 comisiones in materias mapped to grupo=PROG and SalarioPlus(grupo=PROG, rol=PROFESOR).monto = 5000
- **THEN** the calculated plus SHALL be 15000 (3 × 5000)
