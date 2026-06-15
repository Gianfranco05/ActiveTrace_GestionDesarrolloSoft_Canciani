## ADDED Requirements

### Requirement: Materia ORM model (tenant-scoped catalog)
The system SHALL define a Materia ORM model representing a subject/materia in the tenant's catalog. The model SHALL extend BaseModelMixin. Fields:

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK, via BaseModelMixin |
| `tenant_id` | UUID | FK → Tenant(id), via BaseModelMixin |
| `codigo` | String(20) | NOT NULL, unique per tenant (e.g., "PROG_I", "MATE_II") |
| `nombre` | String(200) | NOT NULL (e.g., "Programación I", "Matemática II") |
| `estado` | String(20) | NOT NULL, default "Activa" |
| `created_at` | DateTime | via BaseModelMixin |
| `updated_at` | DateTime | via BaseModelMixin |
| `deleted_at` | DateTime | nullable, via BaseModelMixin |

Table args: UNIQUE(tenant_id, codigo) with partial index WHERE deleted_at IS NULL.

#### Scenario: Create materia with valid fields
- **WHEN** creating a Materia with codigo, nombre, and a valid tenant_id
- **THEN** the Materia SHALL have a UUID id, the provided fields, created_at, and updated_at

#### Scenario: Materia codigo must be unique per tenant
- **WHEN** creating a second Materia with the same codigo and tenant_id
- **THEN** an IntegrityError SHALL be raised

#### Scenario: Same codigo allowed in different tenants
- **WHEN** creating a Materia with the same codigo but different tenant_id
- **THEN** the creation SHALL succeed

#### Scenario: Materia default estado
- **WHEN** creating a Materia without specifying estado
- **THEN** the estado SHALL default to "Activa"

#### Scenario: Materia soft delete
- **WHEN** calling soft_delete on a Materia
- **THEN** deleted_at SHALL be set to the current timestamp

### Requirement: MateriaRepository
The system SHALL provide a MateriaRepository extending BaseRepository[Materia] with:

- All BaseRepository methods (list, get, create, update, soft_delete)
- `get_by_codigo(codigo: str) -> Materia | None` — find by codigo within tenant scope

#### Scenario: Get materia by codigo
- **WHEN** calling get_by_codigo with an existing codigo in the tenant
- **THEN** the Materia SHALL be returned

#### Scenario: Get materia by codigo returns None for missing
- **WHEN** calling get_by_codigo with a non-existent codigo
- **THEN** None SHALL be returned

#### Scenario: Materia is catalog-only
- **WHEN** inspecting the Materia model
- **THEN** it SHALL NOT have carrera_id or any relationship to Carrera/Cohorte (catalog per ADR-006)
