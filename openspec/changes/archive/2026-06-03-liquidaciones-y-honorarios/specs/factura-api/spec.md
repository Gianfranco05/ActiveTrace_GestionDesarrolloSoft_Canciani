## ADDED Requirements

### Requirement: List facturas with filters

The system SHALL expose a GET endpoint to list facturas with filters: usuario_id, cohorte_id, estado (Pendiente/Abonada), date range (cargada_at).

#### Scenario: List all facturas
- **WHEN** FINANZAS calls GET /api/facturas
- **THEN** the system returns all facturas for the tenant ordered by cargada_at descending

#### Scenario: Filter by estado
- **WHEN** FINANZAS calls GET /api/facturas?estado=Pendiente
- **THEN** the system returns only facturas with estado=Pendiente

#### Scenario: Filter by usuario
- **WHEN** FINANZAS calls GET /api/facturas?usuario_id=X
- **THEN** the system returns only facturas for that docente

### Requirement: Create factura

The system SHALL expose a POST endpoint to create a factura. The system SHALL validate that the referenced usuario has `facturador=True`.

#### Scenario: Successful factura creation
- **WHEN** FINANZAS calls POST /api/facturas with valid payload for a facturante usuario
- **THEN** the system creates the factura with estado=Pendiente and returns it

#### Scenario: Periodo format validation
- **WHEN** FINANZAS sends periodo="2026-13" (invalid month)
- **THEN** the system SHALL reject with 422 validation error

### Requirement: Transition factura to Abonada

The system SHALL expose a PUT endpoint to mark a factura as paid (Pendiente → Abonada). The `abonada_at` timestamp SHALL be set automatically.

#### Scenario: Mark factura as paid
- **WHEN** FINANZAS calls PUT /api/facturas/{id}/abonar on a Pendiente factura
- **THEN** estado becomes Abonada and abonada_at is set to current timestamp

#### Scenario: Cannot abonar already paid factura
- **WHEN** FINANZAS calls PUT /api/facturas/{id}/abonar on an Abonada factura
- **THEN** the system SHALL reject with 409 Conflict

### Requirement: Transition factura back to Pendiente

The system SHALL expose a PUT endpoint to revert a factura from Abonada back to Pendiente. The `abonada_at` SHALL be cleared.

#### Scenario: Reopen paid factura
- **WHEN** FINANZAS calls PUT /api/facturas/{id}/reabrir on an Abonada factura
- **THEN** estado becomes Pendiente and abonada_at is set to null

#### Scenario: Cannot reabrir already pending factura
- **WHEN** FINANZAS calls PUT /api/facturas/{id}/reabrir on a Pendiente factura
- **THEN** the system SHALL reject with 409 Conflict

### Requirement: Soft delete factura

The system SHALL expose a DELETE endpoint to soft-delete a factura. Deleted facturas SHALL be excluded from list queries.

#### Scenario: Delete factura
- **WHEN** FINANZAS calls DELETE /api/facturas/{id}
- **THEN** the factura is soft-deleted (deleted_at set)

### Requirement: Permission enforcement on facturas

The system SHALL require `liquidaciones:ver` permission on all factura endpoints.

#### Scenario: Unauthorized access returns 403
- **WHEN** a user without `liquidaciones:ver` attempts any factura endpoint
- **THEN** the system SHALL return 403 Forbidden
