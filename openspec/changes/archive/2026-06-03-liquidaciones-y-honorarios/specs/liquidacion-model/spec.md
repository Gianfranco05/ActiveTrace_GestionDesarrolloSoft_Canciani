## ADDED Requirements

### Requirement: Liquidacion ORM model

The system SHALL persist a `Liquidacion` entity representing the monthly honorarium calculation for a single docente in a specific cohorte. It SHALL store: `monto_base` (from SalarioBase), `monto_plus` (sum of applicable SalarioPlus × comisiones), `total` (base + plus), `es_nexo` flag, `excluido_por_factura` flag, `estado` (Abierta or Cerrada), `rol`, and `comisiones` list. The combination `(tenant_id, cohorte_id, periodo, usuario_id)` SHALL be unique.

#### Scenario: Create liquidation line for a docente
- **WHEN** the calculation engine determines base=50000, plus=15000 for docente X in cohorte Y, periodo 2026-05
- **THEN** a Liquidacion record is persisted with monto_base=50000, monto_plus=15000, total=65000, estado=Abierta

#### Scenario: NEXO flag is set for NEXO rol
- **WHEN** the liquidated docente has rol=NEXO
- **THEN** the Liquidacion record SHALL have es_nexo=True

#### Scenario: Facturante exclusion flag
- **WHEN** the liquidated docente has usuario.facturador=True
- **THEN** the Liquidacion record SHALL have excluido_por_factura=True and total=0

### Requirement: Liquidacion state machine (Abierta → Cerrada)

The Liquidacion `estado` field SHALL follow a strict state machine: Abierta → Cerrada. Once Cerrada, no field of the Liquidacion SHALL be modifiable except soft-delete.

#### Scenario: Close liquidation for a period
- **WHEN** FINANZAS closes the liquidation for cohorte Y, periodo 2026-05
- **THEN** all Liquidacion records for that (cohorte, periodo) transition from Abierta to Cerrada

#### Scenario: Cannot modify closed liquidation
- **WHEN** any attempt is made to update a Liquidacion record with estado=Cerrada
- **THEN** the system SHALL reject with a 422 or 409 error

#### Scenario: Cannot close already closed liquidation
- **WHEN** FINANZAS attempts to close a liquidation period that is already Cerrada
- **THEN** the system SHALL reject with a 409 Conflict

### Requirement: Liquidacion unit is (cohorte, periodo)

The atomic unit of liquidation SHALL be the pair `(cohorte_id, periodo)`. Closing a liquidation SHALL affect all docentes in that cohorte and period simultaneously. Different cohortes SHALL have independent liquidations.

#### Scenario: Close affects all docentes in the period
- **WHEN** cohorte Y has 5 docentes, periodo 2026-05 is closed
- **THEN** all 5 Liquidacion records for that (cohorte, periodo) are transitioned to Cerrada

#### Scenario: Different cohortes have independent liquidations
- **WHEN** cohorte A has liquidacion Cerrada for 2026-05
- **THEN** cohorte B for the same periodo remains unaffected (still Abierta or not yet calculated)
