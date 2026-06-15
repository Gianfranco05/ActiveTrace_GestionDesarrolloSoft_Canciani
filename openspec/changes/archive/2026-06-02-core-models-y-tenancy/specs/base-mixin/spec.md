## ADDED Requirements

### Requirement: Base mixin with primary key

The system SHALL provide a `BaseModelMixin` (declarative mixin) that defines the `id` primary key for all domain entities. The primary key SHALL be a UUID generated with `uuid.uuid4()`.

#### Scenario: Id is auto-generated UUID

- **WHEN** a new entity that inherits from `BaseModelMixin` is created
- **THEN** its `id` field SHALL be automatically populated with a UUID v4 value

### Requirement: Base mixin with tenant_id foreign key

The `BaseModelMixin` SHALL define a `tenant_id` column that is a foreign key referencing `Tenant(id)`. This column SHALL be NOT NULL and indexed.

#### Scenario: Tenant_id is required

- **WHEN** an entity that inherits from `BaseModelMixin` is created without a `tenant_id`
- **THEN** the creation SHALL raise an integrity error (foreign key / NOT NULL violation)

### Requirement: Base mixin with timestamps

The `BaseModelMixin` SHALL define `created_at` and `updated_at` timestamp columns. `created_at` SHALL be set on creation. `updated_at` SHALL be updated on every modification.

#### Scenario: Created_at auto-populates on insert

- **WHEN** a new entity is inserted
- **THEN** its `created_at` SHALL be set to the current UTC timestamp

#### Scenario: Updated_at changes on update

- **WHEN** an entity is updated
- **THEN** its `updated_at` SHALL be set to a timestamp newer than the previous value

### Requirement: Base mixin with soft delete

The `BaseModelMixin` SHALL define a `deleted_at` nullable timestamp column. When set, the record SHALL be considered "deleted" but SHALL remain in the database.

#### Scenario: Deleted_at is null by default

- **WHEN** a new entity is created
- **THEN** its `deleted_at` SHALL be `NULL`

#### Scenario: Deleted_at is set on soft delete

- **WHEN** an entity is soft-deleted via the repository
- **THEN** its `deleted_at` SHALL be set to the current UTC timestamp
- **AND** the record SHALL still exist in the database
