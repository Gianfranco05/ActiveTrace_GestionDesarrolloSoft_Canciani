## ADDED Requirements

### Requirement: Carrera ORM model (tenant-scoped, soft-deletable)
The system SHALL define a Carrera ORM model representing an academic program (carrera) within a tenant. The model SHALL extend BaseModelMixin (UUID PK, tenant_id FK, created_at, updated_at, deleted_at). Fields:

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK, via BaseModelMixin |
| `tenant_id` | UUID | FK → Tenant(id), via BaseModelMixin |
| `codigo` | String(20) | NOT NULL, unique per tenant |
| `nombre` | String(200) | NOT NULL |
| `estado` | String(20) | NOT NULL, default "Activa" |
| `created_at` | DateTime | via BaseModelMixin |
| `updated_at` | DateTime | via BaseModelMixin |
| `deleted_at` | DateTime | nullable, via BaseModelMixin |

Table args: UNIQUE(tenant_id, codigo) with partial index WHERE deleted_at IS NULL.

#### Scenario: Create carrera with valid fields
- **WHEN** creating a Carrera with codigo, nombre, estado, and a valid tenant_id
- **THEN** the Carrera SHALL have a UUID id, the provided fields, created_at, and updated_at

#### Scenario: Carrera codigo must be unique per tenant
- **WHEN** creating a second Carrera with the same codigo and tenant_id
- **THEN** an IntegrityError SHALL be raised

#### Scenario: Same codigo allowed in different tenants
- **WHEN** creating a Carrera with the same codigo but different tenant_id
- **THEN** the creation SHALL succeed

#### Scenario: Carrera default estado
- **WHEN** creating a Carrera without specifying estado
- **THEN** the estado SHALL default to "Activa"

#### Scenario: Carrera soft delete
- **WHEN** calling soft_delete on a Carrera
- **THEN** deleted_at SHALL be set to the current timestamp (not hard deleted)

### Requirement: CarreraRepository
The system SHALL provide a CarreraRepository extending BaseRepository[Carrera] with:

- All BaseRepository methods (list, get, create, update, soft_delete)
- `get_by_codigo(codigo: str) -> Carrera | None` — find by codigo within tenant scope

#### Scenario: Get carrera by codigo
- **WHEN** calling get_by_codigo with an existing codigo in the tenant
- **THEN** the Carrera SHALL be returned

#### Scenario: Get carrera by codigo returns None for missing
- **WHEN** calling get_by_codigo with a non-existent codigo
- **THEN** None SHALL be returned

#### Scenario: Carrera list excludes soft-deleted
- **WHEN** calling list() after soft-deleting a Carrera
- **THEN** the result SHALL NOT include the soft-deleted Carrera
