## Why

C-04 established fine-grained authorization with `require_permission("estructura:gestionar")`. C-05 built the append-only audit log. Now we need the **academic structure** — the backbone of the entire platform. Without C-06, there are no carreras, no cohortes, no materias catalog. C-07 (equipos docentes), C-08 (padron), C-09 (calificaciones), and everything downstream depends on these entities existing.

The KB defines (E1) Carrera, (E2) Cohorte, and (E3) Materia as the foundational academic entities. The product name is *trace* — every academic process traces back to these structures.

## What Changes

- **EstadoRegistro StrEnum** — shared enum `EstadoRegistro("Activa", "Inactiva")` for all academic entity statuses (`backend/app/core/estado_registro.py`)
- **Carrera ORM model** — Programa académico with `codigo` (unique per tenant), `nombre`, `estado`; extends `BaseModelMixin` with soft delete
- **Cohorte ORM model** — Camada/ingreso within a Carrera with `nombre`, `anio`, `vig_desde`, `vig_hasta` (nullable), `estado`; FK to Carrera with cascade
- **Materia ORM model** — Catálogo único de materias del tenant with `codigo` (unique per tenant), `nombre`, `estado`; extends `BaseModelMixin`
- **CarreraRepository** — CRUD for Carrera with `get_by_codigo()`, unique constraint enforcement
- **CohorteRepository** — CRUD for Cohorte with business rule (carrera must be active)
- **MateriaRepository** — CRUD for Materia with `get_by_codigo()`
- **Pydantic schemas** — Create/Update/Response schemas per model with `extra='forbid'`
- **CRUD routers** — `/api/v1/estructura/carreras`, `/cohortes`, `/materias` all guarded by `require_permission("estructura:gestionar")`
- **Alembic migration 005** — creates `carrera`, `cohorte`, `materia` tables with indexes and FKs

## Capabilities

### New Capabilities
- `estructura-carrera`: Carrera ORM model + repository + business rules
- `estructura-cohorte`: Cohorte ORM model + repository + FK cascades
- `estructura-materia`: Materia ORM model + repository (catalog)
- `estructura-enums`: EstadoRegistro shared enum
- `estructura-admin-api`: CRUD endpoints for all 3 entities, guarded by `estructura:gestionar`
- `estructura-migration`: Alembic migration 005

### Modified Capabilities
- `backend/app/models/__init__.py` — export Carrera, Cohorte, Materia
- `backend/app/main.py` — register estructura router (sub-router per entity)

## Impact

- **New enum**: `backend/app/core/estado_registro.py`
- **New models**: `backend/app/models/carrera.py`, `cohorte.py`, `materia.py`
- **New schemas**: `backend/app/schemas/estructura.py`
- **New repositories**: `backend/app/repositories/carrera_repository.py`, `cohorte_repository.py`, `materia_repository.py`
- **New router**: `backend/app/api/v1/routers/estructura.py`
- **New migration**: `backend/alembic/versions/005_estructura_academica.py`
- **Dependencies**: `C-04` (uses `require_permission("estructura:gestionar")`), `C-02` (BaseModelMixin, tenant scope)
