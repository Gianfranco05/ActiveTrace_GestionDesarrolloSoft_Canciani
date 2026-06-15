## ADDED Requirements

### Requirement: View liquidation for a period

The system SHALL expose a GET endpoint to view all liquidaciones for a given (cohorte_id, periodo) with KPI data segmented by general, NEXO, and facturante groups.

#### Scenario: View liquidation list with KPIs
- **WHEN** FINANZAS calls GET /api/liquidaciones?cohorte_id=Y&periodo=2026-05
- **THEN** the system returns the list of Liquidacion records with KPIs: total_general, total_sin_factura, total_nexo, total_facturantes, total_docentes

#### Scenario: Filter by docente
- **WHEN** FINANZAS calls GET /api/liquidaciones?cohorte_id=Y&periodo=2026-05&docente_id=X
- **THEN** the system returns only the Liquidacion record for that specific docente

#### Scenario: No liquidation calculated yet
- **WHEN** FINANZAS calls GET /api/liquidaciones?cohorte_id=Y&periodo=2026-05 and no calculation has been run
- **THEN** the system returns an empty list with zero KPIs

### Requirement: Trigger liquidation calculation

The system SHALL expose a POST endpoint to calculate liquidaciones for a given (cohorte_id, periodo). The calculation SHALL upsert existing Liquidacion records: if a record already exists with estado=Abierta, it SHALL be updated; if none exists, a new one SHALL be created.

#### Scenario: First-time calculation
- **WHEN** FINANZAS calls POST /api/liquidaciones/calcular with cohorte_id=Y, periodo=2026-05
- **THEN** the system computes liquidaciones for all active docentes and persists them

#### Scenario: Recalculation updates open liquidations
- **WHEN** FINANZAS recalculates a period that already has Abierta liquidaciones
- **THEN** the system SHALL update the existing records with new values

#### Scenario: Recalculation blocked on closed liquidation
- **WHEN** FINANZAS attempts to recalculate a period where liquidaciones have estado=Cerrada
- **THEN** the system SHALL reject with 422 error

### Requirement: Close liquidation for a period

The system SHALL expose a POST endpoint to close all liquidaciones in a (cohorte_id, periodo). The close operation SHALL be audited with action code `LIQUIDACION_CERRAR`.

#### Scenario: Successful close
- **WHEN** FINANZAS calls POST /api/liquidaciones/{cohorte_id}/{periodo}/cerrar
- **THEN** all Liquidacion records transition to estado=Cerrada AND an audit record is created with LIQUIDACION_CERRAR

#### Scenario: Close without prior calculation
- **WHEN** FINANZAS attempts to close a period with no liquidaciones
- **THEN** the system SHALL reject with 404 or 422

#### Scenario: Close already closed period
- **WHEN** FINANZAS attempts to close an already Cerrada period
- **THEN** the system SHALL reject with 409 Conflict

### Requirement: Liquidation history

The system SHALL expose a GET endpoint to list closed liquidaciones from previous periods, filterable by cohorte and date range.

#### Scenario: List closed liquidations for a cohorte
- **WHEN** FINANZAS calls GET /api/liquidaciones/historial?cohorte_id=Y
- **THEN** the system returns all Cerrada liquidaciones for that cohorte, ordered by periodo descending

### Requirement: Export liquidation

The system SHALL expose a GET endpoint to export liquidaciones as a downloadable spreadsheet (CSV or XLSX format).

#### Scenario: Export current liquidation
- **WHEN** FINANZAS calls GET /api/liquidaciones/exportar?cohorte_id=Y&periodo=2026-05
- **THEN** the system returns a downloadable file with all liquidation rows

### Requirement: Permission enforcement on liquidaciones

The system SHALL enforce RBAC on all liquidacion endpoints:
- `liquidaciones:ver` for GET endpoints
- `liquidaciones:calcular` for POST /calcular
- `liquidaciones:cerrar` for POST /cerrar
- `liquidaciones:exportar` for GET /exportar

#### Scenario: Unauthorized access returns 403
- **WHEN** a user without `liquidaciones:calcular` attempts to POST /api/liquidaciones/calcular
- **THEN** the system SHALL return 403 Forbidden
