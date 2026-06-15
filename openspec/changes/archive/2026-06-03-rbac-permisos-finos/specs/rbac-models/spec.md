## ADDED Requirements

### Requirement: Rol model (tenant-scoped)
The system SHALL define a Rol ORM model representing a named role within a tenant. The model SHALL extend BaseModelMixin (UUID PK, tenant_id FK, timestamps, soft delete). Fields: nombre (String 50, unique per tenant), descripcion (Text, nullable). Constraint: UNIQUE(tenant_id, nombre) with partial index WHERE deleted_at IS NULL.

#### Scenario: Create rol with valid fields
- **WHEN** creating a Rol with nombre, descripcion, and a valid tenant_id
- **THEN** the Rol SHALL have a UUID id, the provided tenant_id, nombre, descripcion, created_at, and updated_at

#### Scenario: Rol nombre must be unique per tenant
- **WHEN** creating a second Rol with the same nombre and tenant_id as an existing active Rol
- **THEN** an IntegrityError SHALL be raised

#### Scenario: Same rol nombre allowed in different tenants
- **WHEN** creating a Rol with the same nombre but a different tenant_id
- **THEN** the creation SHALL succeed

#### Scenario: Rol soft delete
- **WHEN** deleting a Rol
- **THEN** deleted_at SHALL be set to the current timestamp (not hard deleted)

### Requirement: Permiso model (tenant-agnostic)
The system SHALL define a Permiso ORM model representing an atomic permission code. The model SHALL NOT be tenant-scoped (shared catalog across tenants). Fields: codigo (String 80, unique, format `modulo:accion`), descripcion (Text, nullable). Extends BaseModelMixin for id, timestamps.

#### Scenario: Create permiso with valid codigo
- **WHEN** creating a Permiso with codigo = "calificaciones:importar" and a descripcion
- **THEN** the Permiso SHALL have a UUID id, the provided codigo, and descripcion

#### Scenario: Permiso codigo must be unique
- **WHEN** creating a second Permiso with the same codigo
- **THEN** an IntegrityError SHALL be raised

#### Scenario: Permiso codigo format
- **WHEN** creating a Permiso with codigo
- **THEN** the codigo SHALL match the pattern `modulo:accion` (lowercase, no spaces)

### Requirement: RolPermiso model (many-to-many)
The system SHALL define a RolPermiso ORM model representing the many-to-many relationship between Rol and Permiso. Fields: rol_id (FK to Rol), permiso_id (FK to Permiso). Constraint: UNIQUE(rol_id, permiso_id). RolPermiso is tenant-scoped via the Rol (tenant_id on Rol).

#### Scenario: Assign permiso to rol
- **WHEN** creating a RolPermiso with a valid rol_id and permiso_id
- **THEN** the relationship SHALL exist and be queryable from both sides

#### Scenario: Duplicate rol-permiso assignment is rejected
- **WHEN** creating a second RolPermiso with the same rol_id and permiso_id
- **THEN** an IntegrityError SHALL be raised

#### Scenario: RolPermiso cascade delete
- **WHEN** a Rol is soft-deleted
- **THEN** its RolPermiso associations SHALL NOT prevent querying the permiso catalog

### Requirement: Effective permissions query
The system SHALL provide a query that returns all distinct permiso codigos for a given list of role names. The query SHALL join rol_permiso → permiso → rol and return only the codigo strings.

#### Scenario: Get effective permissions for roles
- **WHEN** querying effective permissions for roles ["ADMIN", "PROFESOR"]
- **THEN** the result SHALL contain the union of all permissions assigned to either role

#### Scenario: Empty roles list returns empty set
- **WHEN** querying effective permissions for an empty list of roles
- **THEN** the result SHALL be an empty set

#### Scenario: Non-existent role name returns empty contribution
- **WHEN** querying effective permissions with a role name that does not exist in the tenant
- **THEN** that role contributes zero permissions to the result

### Requirement: RolPermisoRepository
The system SHALL provide an RbacRepository with methods:
- `get_effective_permissions(db, role_names: list[str]) -> set[str]` — returns distinct permission codigos for the given role names
- `get_roles_by_tenant(db, tenant_id) -> list[Rol]` — lists all non-deleted roles for a tenant
- `get_permisos_catalog(db) -> list[Permiso]` — lists all permissions (global catalog)
- `assign_permisos_to_rol(db, rol_id, permiso_ids: list[UUID])` — replaces all permissions for a role (clear + insert)

#### Scenario: Assign permissions to role replaces all
- **WHEN** calling assign_permisos_to_rol with a new set of permiso_ids for a rol
- **THEN** all previous RolPermiso entries for that rol SHALL be removed and the new ones inserted atomically
