## ADDED Requirements

### Requirement: Calculate liquidation applying RN-34 formula

The system SHALL compute the liquidation for all docentes in a given `(cohorte_id, periodo)` by applying the formula:

`Total = Base(rol, mes) + Σ(Plus(grupo, rol) × N_comisiones_grupo)`

Where:
- `Base(rol, mes)` is the SalarioBase entry for the docente's rol that is temporally valid for the period
- `Plus(grupo, rol)` is the SalarioPlus entry for each (grupo, rol) pair valid for the period
- `N_comisiones_grupo` is the number of comisiones the docente has in materias mapped to that grupo
- The grupo for a materia is resolved via GrupoMateria mapping

#### Scenario: Full calculation with base and multiple plus
- **WHEN** calculating for docente with rol=PROFESOR, base=50000, 3 comisiones in grupo=PROG (plus=5000), 1 comision in grupo=BD (plus=3000)
- **THEN** monto_base=50000, monto_plus=(3×5000 + 1×3000)=18000, total=68000

#### Scenario: Docente with no plus (no grupo mappings)
- **WHEN** a docente has comisiones in materias with no GrupoMateria mapping
- **THEN** monto_plus=0 and total=monto_base

#### Scenario: Docente with no active base salary
- **WHEN** a docente's rol has no SalarioBase entry valid for the period
- **THEN** the docente SHALL be excluded from the liquidation and flagged in the response

#### Scenario: Docente with incomplete banking data
- **WHEN** a docente lacks CBU or alias_cbu in their Usuario record
- **THEN** the docente SHALL be excluded from the liquidation and flagged as "datos_bancarios_incompletos" in the response

### Requirement: Temporal validity resolution for salary entries

The system SHALL resolve which SalarioBase and SalarioPlus entries are active for a given period by filtering: `vig_desde <= mes_start AND (vig_hasta IS NULL OR vig_hasta >= mes_end)`.

#### Scenario: Base salary valid for entire period
- **WHEN** SalarioBase has vig_desde=2026-01-01, vig_hasta=NULL, period=2026-05
- **THEN** the entry is selected as active

#### Scenario: Base salary valid only from a certain date
- **WHEN** SalarioBase has vig_desde=2026-04-01, vig_hasta=NULL, period=2026-03
- **THEN** the entry is NOT selected (vig_desde is after the period)

#### Scenario: Base salary expired before the period
- **WHEN** SalarioBase has vig_desde=2026-01-01, vig_hasta=2026-04-30, period=2026-05
- **THEN** the entry is NOT selected (vig_hasta is before the period)

### Requirement: Resolve Plus via GrupoMateria mapping

The system SHALL determine which grupo a materia belongs to via the GrupoMateria mapping table. Each materia can belong to multiple grupos. For each comision of a docente, the system SHALL resolve the materia's grupos, then for each unique grupo, count the total comisiones and multiply by the matching SalarioPlus.monto.

#### Scenario: One materia in one grupo
- **WHEN** materia MAT-01 is mapped to grupo=PROG and docente has 2 comisiones in MAT-01
- **THEN** N_comisiones for grupo PROG = 2

#### Scenario: Same materia mapped to multiple grupos
- **WHEN** materia MAT-01 is mapped to both grupo=PROG and grupo=ING
- **THEN** both grupos get N_comisiones=1 for each comision in MAT-01 (plus accumulates from both groups)

#### Scenario: Materia not mapped to any grupo
- **WHEN** a materia has no GrupoMateria entry
- **THEN** that materia contributes 0 to all Plus calculations

### Requirement: Detect docente roles from Asignacion

The system SHALL determine the rol under which a docente is liquidated from their active Asignacion records in the cohorte. If a docente has multiple Asignacion records with different roles, the system SHALL use the most specific rol applicable (or create separate liquidation lines per rol).

#### Scenario: Single-rol docente
- **WHEN** a docente has Asignacion rol=PROFESOR active in the cohorte
- **THEN** the liquidation uses rol=PROFESOR for SalarioBase lookup

#### Scenario: Multi-rol docente
- **WHEN** a docente has Asignacion records with both rol=PROFESOR and rol=COORDINADOR active in the cohorte
- **THEN** the system SHALL create separate Liquidacion records, one per rol, each with the corresponding base and plus

### Requirement: NEXO and Facturante segmentation in calculation

The system SHALL flag each Liquidacion record with `es_nexo=True` when the rol is NEXO, and `excluido_por_factura=True` when the docente's usuario.facturador is True. Facturante liquidaciones SHALL have total=0.

#### Scenario: NEXO docente generates separate segment
- **WHEN** calculating liquidation for a docente with rol=NEXO
- **THEN** the Liquidacion record has es_nexo=True and its total is included in the overall sum

#### Scenario: Facturante excluded from monetary total
- **WHEN** calculating liquidation for a facturante docente
- **THEN** the Liquidacion record has excluido_por_factura=True, total=0
