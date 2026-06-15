## ADDED Requirements

### Requirement: Cohorte ORM model (tenant-scoped, FK to Carrera)
The system SHALL define a Cohorte ORM model representing a cohort/class within a Carrera. The model SHALL extend BaseModelMixin. Fields:

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK, via BaseModelMixin |
| `tenant_id` | UUID | FK → Tenant(id), via BaseModelMixin |
| `carrera_id` | UUID | FK → Carrera(id), NOT NULL, ON DELETE RESTRICT |
| `nombre` | String(50) | NOT NULL (e.g., "AGO-2025", "MAR-2026") |
| `anio` | Integer | NOT NULL |
| `vig_desde` | Date | NOT NULL |
| `vig_hasta` | Date | nullable (NULL = abierta/sin cierre) |
| `estado` | String(20) | NOT NULL, default "Activa" |
| `created_at` | DateTime | via BaseModelMixin |
| `updated_at` | DateTime | via BaseModelMixin |
| `deleted_at` | DateTime | nullable, via BaseModelMixin |

Table args: UNIQUE(tenant_id, carrera_id, nombre) with partial index WHERE deleted_at IS NULL.
FK(tenant_id, carrera_id) → Carrera(id) with ON DELETE RESTRICT.

#### Scenario: Create cohorte with valid fields
- **WHEN** creating a Cohorte with carrera_id, nombre, anio, vig_desde, and a valid tenant_id
- **THEN** the Cohorte SHALL have a UUID id, the provided fields, created_at, and updated_at

#### Scenario: Cohorte nombre must be unique per tenant per carrera
- **WHEN** creating a second Cohorte with the same nombre, carrera_id, and tenant_id
- **THEN** an IntegrityError SHALL be raised

#### Scenario: Cohorte default estado
- **WHEN** creating a Cohorte without specifying estado
- **THEN** the estado SHALL default to "Activa"

#### Scenario: Cohorte vig_hasta nullable
- **WHEN** creating a Cohorte without vig_hasta
- **THEN** vig_hasta SHALL be NULL (open cohort)

#### Scenario: Cohorte FK to Carrera is enforced
- **WHEN** creating a Cohorte with a non-existent carrera_id
- **THEN** an IntegrityError SHALL be raised

#### Scenario: Cohorte soft delete
- **WHEN** calling soft_delete on a Cohorte
- **THEN** deleted_at SHALL be set to the current timestamp

### Requirement: Cohorte business rule — Carrera must be active
The system SHALL enforce that a Cohorte can only be created/updated to "Activa" if its referenced Carrera is in "Activa" estado. This rule SHALL be enforced at the SERVICE layer, not DB.

#### Scenario: Create cohorte with inactive carrera rejected
- **WHEN** creating a Cohorte with estado "Activa" for a Carrera with estado "Inactiva"
- **THEN** the operation SHALL be rejected with an error

#### Scenario: Create cohorte with active carrera succeeds
- **WHEN** creating a Cohorte with estado "Activa" for a Carrera with estado "Activa"
- **THEN** the operation SHALL succeed

#### Scenario: Update carrera to inactive with active cohortes
- **WHEN** updating a Carrera's estado to "Inactiva" AND there are active Cohortes linked
- **THEN** the update SHALL be allowed (the rule is about creating cohortes, not blocking carrera deactivation)

### Requirement: CohorteRepository
The system SHALL provide a CohorteRepository extending BaseRepository[Cohorte] with:

- All BaseRepository methods (list, get, create, update, soft_delete)
- `get_by_carrera(carrera_id: UUID) -> list[Cohorte]` — filter by carrera within tenant
- `get_activas_by_carrera(carrera_id: UUID) -> list[Cohorte]` — only "Activa" cohortes for a carrera

#### Scenario: Get cohortes by carrera
- **WHEN** calling get_by_carrera with a valid carrera_id
- **THEN** all non-deleted cohortes for that carrera SHALL be returned

#### Scenario: Get cohortes list filtered by carrera_id
- **WHEN** calling list(carrera_id=<uuid>)
- **THEN** only cohortes for that carrera SHALL be returned (via base repository filter)
