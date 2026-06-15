## ADDED Requirements

### Requirement: Factura ORM model

The system SHALL persist a `Factura` entity representing a billing document for a facturante docente. It SHALL store: `usuario_id` (with facturador=true), optional `cohorte_id`, `periodo` (YYYY-MM), `detalle` (free text), optional `referencia_archivo` (opaque storage pointer), optional `tamano_kb`, `estado` (Pendiente or Abonada), `cargada_at`, and optional `abonada_at`.

#### Scenario: Create factura for a facturante docente
- **WHEN** FINANZAS creates a Factura for usuario X, periodo 2026-05, detalle "Honorarios programación"
- **THEN** the system persists the record with estado=Pendiente and cargada_at set to current timestamp

#### Scenario: Factura with cohorte association
- **WHEN** FINANZAS creates a Factura with cohorte_id=Y
- **THEN** the factura is linked to that cohorte for filtering and reporting

#### Scenario: Factura without cohorte (global)
- **WHEN** FINANZAS creates a Factura with cohorte_id=null
- **THEN** the factura is global and not scoped to any specific cohorte

### Requirement: Factura state transitions (Pendiente ↔ Abonada)

The Factura `estado` field SHALL support bidirectional transitions between Pendiente and Abonada. When transitioning to Abonada, `abonada_at` SHALL be set automatically. When transitioning back to Pendiente, `abonada_at` SHALL be cleared.

#### Scenario: Mark factura as paid (Pendiente → Abonada)
- **WHEN** FINANZAS confirms payment of a factura with estado=Pendiente
- **THEN** estado transitions to Abonada and abonada_at is set to the current timestamp

#### Scenario: Reopen paid factura (Abonada → Pendiente)
- **WHEN** FINANZAS needs to revert a factura from Abonada back to Pendiente
- **THEN** estado transitions to Pendiente and abonada_at is set to null

### Requirement: Only facturante docentes can have facturas

The system SHALL validate at creation time that the `usuario_id` referenced by a Factura belongs to a user with `facturador=True`.

#### Scenario: Create factura for non-facturante user rejected
- **WHEN** FINANZAS attempts to create a Factura for a usuario with facturador=False
- **THEN** the system SHALL reject with a 422 error indicating the user is not a facturante

#### Scenario: Create factura for facturante user accepted
- **WHEN** FINANZAS creates a Factura for a usuario with facturador=True
- **THEN** the system SHALL accept and persist the record
