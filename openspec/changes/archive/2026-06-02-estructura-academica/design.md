## Context

C-04 delivered the authorization layer with `require_permission("estructura:gestionar")`. C-05 delivered the append-only audit log. C-06 builds the academic structure foundation — Carreras, Cohortes, and Materias — that every downstream domain change (C-07 through C-18) depends on.

The KB defines E1 (Carrera), E2 (Cohorte), and E3 (Materia). Governance is **MEDIO** — standard domain logic with no security invariants.

## Goals / Non-Goals

**Goals:**
- EstadoRegistro shared StrEnum for all academic entity statuses
- Carrera ORM model + repository per D1–D5
- Cohorte ORM model + repository with FK to Carrera and business rule (carrera must be active)
- Materia ORM model + repository (catalog-only per ADR-006)
- Pydantic schemas per model (Create/Update/Response) with `extra='forbid'`
- CRUD routers for all 3 entities, guarded by `estructura:gestionar`
- Alembic migration 005 with carrera, cohorte, materia tables
- Soft delete on all 3 models via BaseModelMixin

**Non-Goals:**
- `Dictado` model (Materia instance per Carrera×Cohorte) — emerges in C-07 via Profesor Asignaciones
- Import/export of academic structure (future change)
- Bulk operations — CRUD only, single entity per request
- Frontend UI — C-21 shell covers this later

## Decisions

### D1 — ADR-006: Materia is catalog-only; Dictado emerges at C-07

Materia in C-06 is the **catalog definition** — unique per tenant, no relationship to Carrera or Cohorte. The `Dictado` concept (a Materia taught in a specific Carrera×Cohorte combination) is NOT modeled as a separate entity here. It emerges naturally at C-07 when PROFESOR Asignaciones link a Materia with a Carrera and Cohorte.

This avoids premature complexity. The dictado-specific fields (profesor asignado, horarios, aula, etc.) belong in C-07, not C-06.

### D2 — EstadoRegistro shared StrEnum

```python
class EstadoRegistro(str, Enum):
    ACTIVA = "Activa"
    INACTIVA = "Inactiva"
```

Used across all 3 entities. Alternative was individual enums per model (CarreraEstado, CohorteEstado, MateriaEstado), but since all share the exact same semantics ("Activa" ↔ usable, "Inactiva" ↔ not usable), a shared enum is cleaner. If a model ever needs a different set of states, we split then.

### D3 — Soft delete via BaseModelMixin

All 3 models extend BaseModelMixin from C-02, providing:
- `id`: UUID PK
- `tenant_id`: UUID FK → Tenant
- `created_at`, `updated_at`: timestamps
- `deleted_at`: nullable, soft delete

Soft delete is important for academic structure — carreras/materias can be "deactivated" via `estado` (soft business rule) OR `soft_delete` (harder boundary). The repository pattern automatically excludes soft-deleted records.

### D4 — Carrera inactiva → no cohortes activas

Business rule enforced at the SERVICE layer, not DB. When creating/updating a Cohorte, the service checks `carrera.estado == EstadoRegistro.ACTIVA` BEFORE persisting. If the Carrera is inactive, the operation is rejected with HTTP 409.

This is correct because:
1. It's a business rule, not a data integrity constraint
2. The rule could change (e.g., "allow cohortes but warn")
3. DB constraints can't express conditional logic like "carrera estado = Activa"

### D5 — Protection via require_permission

All CRUD endpoints on all 3 routers use `require_permission("estructura:gestionar")` from C-04. Only ADMIN and COORDINADOR roles have this permission (seeded in C-04).

Read endpoints (GET list, GET by id) ALSO require `estructura:gestionar` — no public read access to academic structure. If public read is needed later, a separate `estructura:ver` permission can be added.

### D6 — Individual repositories, not a single EstructuraRepository

Each entity gets its own repository (CarreraRepository, CohorteRepository, MateriaRepository) extending `BaseRepository[T]`. This is cleaner than a single monolithic `EstructuraRepository` because:
- Each entity has unique query methods (e.g., `get_by_codigo()` for Carrera/Materia, `get_by_carrera()` for Cohorte)
- Follows the Single Responsibility Principle
- Matches the pattern from C-03/C-04

### D7 — Cohorte FK to Carrera with CASCADE behavior

Cohorte has a `carrera_id` FK to Carrera. When a Carrera is soft-deleted, the FK constraint is checked — because it's soft delete (not hard), descendants remain accessible. Cascade behavior:
- ON DELETE RESTRICT (prevent hard delete of Carrera with cohortes)
- Soft delete of Carrera does NOT cascade to Cohortes (they remain queryable but can be individually retired)

### D8 — Schemas per model (Create/Update/Response)

| Schema | Fields |
|--------|--------|
| `CarreraCreate` | codigo, nombre, estado? (default "Activa") |
| `CarreraUpdate` | codigo?, nombre?, estado? |
| `CarreraResponse` | id, tenant_id, codigo, nombre, estado, created_at, updated_at |
| `CohorteCreate` | carrera_id, nombre, anio, vig_desde, vig_hasta?, estado? |
| `CohorteUpdate` | nombre?, anio?, vig_desde?, vig_hasta?, estado? |
| `CohorteResponse` | id, tenant_id, carrera_id, nombre, anio, vig_desde, vig_hasta, estado, created_at, updated_at |
| `MateriaCreate` | codigo, nombre, estado? |
| `MateriaUpdate` | codigo?, nombre?, estado? |
| `MateriaResponse` | id, tenant_id, codigo, nombre, estado, created_at, updated_at |

All schemas use `model_config = ConfigDict(extra='forbid', from_attributes=True)`.
List responses use `{items: [...], total: int, offset: int, limit: int}` pattern from C-05.

### D9 — Router structure

A single `estructura.py` router module with 3 sub-routers (APIRouter with prefix), all registered under `/api/v1/estructura/`:

| Prefix | Router | Endpoints |
|--------|--------|-----------|
| `/api/v1/estructura/carreras` | `carreras_router` | GET /, POST /, GET /{id}, PUT /{id}, DELETE /{id} |
| `/api/v1/estructura/cohortes` | `cohortes_router` | GET /, POST /, GET /{id}, PUT /{id}, DELETE /{id} |
| `/api/v1/estructura/materias` | `materias_router` | GET /, POST /, GET /{id}, PUT /{id}, DELETE /{id} |

All guarded by `Depends(require_permission("estructura:gestionar"))`.

### D10 — Migration 005 structure

```python
# 005_estructura_academica.py
# Creates:
#   - carrera (codigo VARCHAR(20), nombre VARCHAR(200), estado VARCHAR(20))
#   - cohorte (carrera_id FK, nombre VARCHAR(50), anio INTEGER, vig_desde DATE, vig_hasta DATE nullable, estado VARCHAR(20))
#   - materia (codigo VARCHAR(20), nombre VARCHAR(200), estado VARCHAR(20))
# All extend BaseModelMixin fields: id UUID PK, tenant_id FK, timestamps, soft delete
# Indexes:
#   - carrera: UNIQUE(tenant_id, codigo) WHERE deleted_at IS NULL
#   - cohorte: UNIQUE(tenant_id, carrera_id, nombre) WHERE deleted_at IS NULL
#   - materia: UNIQUE(tenant_id, codigo) WHERE deleted_at IS NULL
#   - cohorte: FK(tenant_id, carrera_id) → carrera
```

## Risks / Trade-offs

- **[EstadoRegistro compartido]** → If a model needs different states later (e.g., Materia with "Borrador"), we must split enums. Acceptable risk — change is a simple refactor.
- **[Sin Dictado model]** → C-07 must create it. If C-07 is delayed, Materia + Carrera + Cohorte exist but cannot be linked through a Dictado. C-06 is explicitly scoped to catalog-only.
- **[Sin bulk operations]** → Importing a full academic structure (e.g., 50 materias from CSV) requires 50 POST calls. Bulk import is deferred to a future change.
- **[Sin endpoints públicos]** → Currently `estructura:gestionar` required for reads too. If we need read-only access for PROFESOR/TUTOR, we add `estructura:ver` permission in C-04 seed and relax the guard.

## Migration Plan

1. Implement `EstadoRegistro` enum in `core/estado_registro.py`
2. Implement Carrera model in `models/carrera.py` + update `models/__init__.py`
3. Implement Cohorte model in `models/cohorte.py` + FK references
4. Implement Materia model in `models/materia.py`
5. Implement all Pydantic schemas in `schemas/estructura.py`
6. Implement CarreraRepository in `repositories/carrera_repository.py`
7. Implement CohorteRepository in `repositories/cohorte_repository.py`
8. Implement MateriaRepository in `repositories/materia_repository.py`
9. Implement router in `api/v1/routers/estructura.py` + register in main.py
10. Generate Alembic migration 005
11. Run full test suite (TDD: RED → GREEN → TRIANGULATE per task)

## Open Questions

- **¿Necesitamos un endpoint para obtener cohortes filtradas por carrera?** Decisión: sí — `GET /api/v1/estructura/cohortes?carrera_id=<uuid>`. Es un filtro directo en el repository.
- **¿Debemos auditar las operaciones CRUD?** Decisión: no en C-06. Cuando se defina el mecanismo de auditoría automática (posiblemente C-19), las operaciones sobre estructura académica se auditarán retroactivamente. Por ahora, el audit log existe pero no lo usamos — es opt-in desde cada service.
