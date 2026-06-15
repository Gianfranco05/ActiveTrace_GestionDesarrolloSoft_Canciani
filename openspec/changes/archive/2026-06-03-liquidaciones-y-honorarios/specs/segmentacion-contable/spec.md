## ADDED Requirements

### Requirement: Three-segment liquidation view

The system SHALL group liquidacion results into three segments for the view API response:
1. **General**: non-NEXO, non-facturante docentes
2. **NEXO**: docentes with es_nexo=True
3. **Facturantes**: docentes with excluido_por_factura=True

#### Scenario: Segmented response structure
- **WHEN** FINANZAS calls GET /api/liquidaciones?cohorte_id=Y&periodo=2026-05
- **THEN** the response includes separate arrays for general, nexo, and facturantes segments

#### Scenario: NEXO segment populated
- **WHEN** a NEXO docente exists in the liquidation
- **THEN** the NEXO docente appears in the nexo segment AND their total is included in the KPIs' total_general

#### Scenario: Facturantes excluded from monetary KPIs
- **WHEN** facturante docentes exist in the liquidation
- **THEN** they appear in the facturantes segment AND are excluded from total_sin_factura KPI

### Requirement: KPI computation for liquidation view

The system SHALL compute the following KPIs for the liquidation view:
- `total_general`: Sum of `total` for all liquidaciones (including NEXO, excluding facturantes)
- `total_sin_factura`: Same as `total_general` (the amount to be paid by the institution)
- `total_nexo`: Sum of `total` where `es_nexo=True`
- `total_facturantes`: Count of liquidaciones where `excluido_por_factura=True`
- `total_docentes`: Total count of liquidacion records

#### Scenario: KPIs with mixed segments
- **WHEN** liquidation has: 3 general (100k total), 2 NEXO (40k total), 1 facturante (0 total)
- **THEN** total_general=140000, total_sin_factura=140000, total_nexo=40000, total_facturantes=1, total_docentes=6

#### Scenario: KPIs with only general segment
- **WHEN** liquidation has only general docentes, no NEXO and no facturantes
- **THEN** total_general = sum of all general, total_nexo=0, total_facturantes=0

### Requirement: NEXO amounts included in total

Per RN-36, the system SHALL include NEXO amounts in the `total_general` KPI. The NEXO segment is visually separated but NOT financially excluded from the institution's payment total.

#### Scenario: Total includes NEXO
- **WHEN** the general segment totals 100000 and NEXO segment totals 40000
- **THEN** total_general = 140000 (both included)

### Requirement: Facturante amounts excluded from total

Per RN-35, the system SHALL exclude facturante liquidaciones (with `excluido_por_factura=True`) from the `total_general` KPI. Facturantes are displayed separately for informational purposes.

#### Scenario: Facturantes excluded from total
- **WHEN** the general segment totals 100000 and facturante segment has 3 entries with total=0
- **THEN** total_general = 100000 (facturantes not included in monetary sum)
