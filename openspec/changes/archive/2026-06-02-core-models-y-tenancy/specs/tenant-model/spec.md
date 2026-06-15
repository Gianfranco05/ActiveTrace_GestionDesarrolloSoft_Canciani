## ADDED Requirements

### Requirement: Tenant entity definition

The system SHALL have a `Tenant` entity that serves as the root of the data model. Every domain entity SHALL reference a tenant via `tenant_id`.

#### Scenario: Tenant has all required fields

- **WHEN** a Tenant record is created
- **THEN** it SHALL have: `id` (UUID primary key, auto-generated), `name` (string, unique, not null), `slug` (string, unique, not null, indexed), `is_active` (boolean, default True), `created_at` (datetime, auto), `updated_at` (datetime, auto)

#### Scenario: Tenant slug is unique

- **WHEN** two Tenant records are created with the same `slug`
- **THEN** the second creation SHALL raise an integrity error (unique constraint violation)

#### Scenario: Tenant name is unique

- **WHEN** two Tenant records are created with the same `name`
- **THEN** the second creation SHALL raise an integrity error

### Requirement: Tenant as root of isolation

The `Tenant` entity SHALL be the root of data isolation. No data from one tenant SHALL be visible to users of another tenant.

#### Scenario: Default tenant exists after migration

- **WHEN** migration 001 is applied
- **THEN** there SHALL be a tenant record with `slug = "default"` seeded in the database

### Requirement: Tenant is uuid-based

The Tenant primary key SHALL be a UUID (not an auto-increment integer), following the project convention that all entity identities are UUIDs.

#### Scenario: Tenant id is a UUID

- **WHEN** a Tenant is created
- **THEN** its `id` field SHALL be of type `uuid.UUID`
