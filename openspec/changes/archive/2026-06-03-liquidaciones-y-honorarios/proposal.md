## Why

C-07 delivered the user model with `facturador` flag and banking data (CBU, alias, banco), and C-06 provided the academic structure foundation (carreras, cohortes, materias). But the institution cannot operate financially: there is no salary grid, no liquidation calculation, no billing workflow for facturantes. C-18 builds the complete financial module — the system that determines how every docente is paid each month. RN-34 defines the formula: `Total = Base(rol) + Σ(Plus(categoría, rol) × N_comisiones)`. Without this, the FINANZAS role has nothing to operate.

## What Changes

- **SalarioBase model** (E17) — per-rol base salary with `vig_desde`/`vig_hasta`. Only one entry can be active per rol at any point in time.
- **SalarioPlus model** (E18) — additional payment per `(grupo, rol)` pair, with temporal validity. `grupo` is a configurable key (e.g., "PROG", "BD") that maps to a set of materias.
- **Liquidacion model** (E19) — period summary per docente: `monto_base` (from SalarioBase), `monto_plus` (sum of applicable SalarioPlus), `total = base + plus`, `es_nexo` flag, `excluido_por_factura` flag, `estado` (Abierta/Cerrada). Unit of liquidation is `(cohorte, periodo)` per RN-37.
- **Factura model** (E20) — billing document for facturante docentes: docente, periodo, detalle, referencia_archivo, tamano_kb, estado (Pendiente/Abonada).
- **Liquidation calculation service** — computes `Total = Base(rol, mes) + Σ(Plus(grupo, rol) × comisiones_activas)` per RN-34. Resolves base and plus by temporal validity. Segments NEXO separately.
- **Salary grid ABM** — CRUD for SalarioBase and SalarioPlus with temporal validity enforcement (RN-31, RN-32, RN-33). No overlapping intervals per rol/grupo.
- **Liquidation close** — transitions estado Abierta → Cerrada, making the record immutable (RN-22). Audited as `LIQUIDACION_CERRAR`.
- **Factura ABM** — CRUD for facturas with status transitions (Pendiente → Abonada). Segregated from general liquidation per RN-35.
- **KPI separation** — the liquidation view exposes three segments: general (non-facturantes), NEXO (included in total), and facturantes (excluded from total). KPIs: "Total sin factura" and "Total con factura" (RN-38).
- **Pydantic schemas** for all models: request DTOs, response DTOs, list views.
- **Liquidaciones router** — `/api/liquidaciones/*` with guards `liquidaciones:*`.
- **Facturas router** — `/api/facturas/*` with guards `liquidaciones:*` (FINANZAS).
- **Alembic migration 0NN** — creates `salario_base`, `salario_plus`, `liquidacion`, `factura` tables.

## Capabilities

### New Capabilities
- `salario-base-model`: SalarioBase ORM model with temporal validity constraints
- `salario-plus-model`: SalarioPlus ORM model with grupo × rol key
- `liquidacion-model`: Liquidacion ORM model with derived total and state machine
- `factura-model`: Factura ORM model for facturante billing
- `calculo-liquidacion`: Service that computes monthly liquidation per RN-34 (base + sum of plus × comisiones). Resolves temporal validity for base and plus entries.
- `grilla-salarial-api`: API endpoints for SalarioBase and SalarioPlus ABM with temporal validity enforcement
- `liquidacion-api`: API endpoints for liquidation view (F10.1), close (F10.2), history (F10.3), and KPI segmentation (F10.6)
- `factura-api`: API endpoints for factura ABM (F10.5) with Pendiente ↔ Abonada state transitions
- `segmentacion-contable`: Business logic for separating facturantes from general liquidation, NEXO segment, and KPI computation (RN-36, RN-38)

### Modified Capabilities
- `backend/app/core/audit_codes.py` — add `LIQUIDACION_CERRAR` action code
- `backend/app/core/permissions.py` — add `liquidaciones:ver`, `liquidaciones:calcular`, `liquidaciones:cerrar`, `liquidaciones:exportar`, `liquidaciones:configurar-salarios`
- `backend/app/models/__init__.py` — export SalarioBase, SalarioPlus, Liquidacion, Factura
- `backend/app/main.py` — register liquidaciones and facturas routers

## Impact

- **New models**: `backend/app/models/salario_base.py`, `backend/app/models/salario_plus.py`, `backend/app/models/liquidacion.py`, `backend/app/models/factura.py`
- **New schemas**: `backend/app/schemas/liquidacion.py`, `backend/app/schemas/factura.py`
- **New repositories**: `backend/app/repositories/salario_repository.py`, `backend/app/repositories/liquidacion_repository.py`, `backend/app/repositories/factura_repository.py`
- **New services**: `backend/app/services/liquidacion_service.py`, `backend/app/services/factura_service.py`
- **New routers**: `backend/app/api/v1/routers/liquidaciones.py`, `backend/app/api/v1/routers/facturas.py`
- **New migration**: `backend/alembic/versions/0NN_liquidaciones_y_honorarios.py`
- **Dependencies**: C-06 (estructura-academica — Materia, Cohorte), C-07 (usuarios-y-asignaciones — Usuario, Asignacion), C-05 (audit-log)
- **⚠️ PA-22 remains open**: the exact set of Plus group keys (PROG, BD, ING, MAT, etc.) and their mapping to materias is not defined. The design will treat `grupo` as a free-text configurable key managed by FINANZAS, with mapping to materias stored in a tenant configuration table.
- **⚠️ PA-24 remains open**: whether facturas must link to specific comisiones or are global per docente. The design will support both via an optional `cohorte_id` FK on Factura.
