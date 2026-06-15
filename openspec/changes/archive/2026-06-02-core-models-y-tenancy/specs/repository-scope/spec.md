## ADDED Requirements

### Requirement: Generic repository with mandatory tenant scope

The system SHALL provide a `BaseRepository` generic class that receives `tenant_id` at construction and applies it as a mandatory filter on all queries. Every SELECT, UPDATE, and DELETE query SHALL include `WHERE tenant_id = :tid`.

#### Scenario: List filters by tenant_id

- **WHEN** `repository.list()` is called
- **THEN** the query SHALL include `WHERE tenant_id = :tid AND deleted_at IS NULL`

#### Scenario: Get filters by tenant_id and id

- **WHEN** `repository.get(id)` is called
- **THEN** the query SHALL include `WHERE id = :id AND tenant_id = :tid AND deleted_at IS NULL`

#### Scenario: Create sets tenant_id from context

- **WHEN** `repository.create(data)` is called
- **THEN** the created record SHALL have its `tenant_id` set to the repository's `tenant_id` value
- **AND** if `data` already contains a `tenant_id`, it SHALL be overridden by the repository's value

### Requirement: Soft delete via repository

The repository SHALL implement `soft_delete(id)` that sets `deleted_at` to the current timestamp instead of deleting the record. The operation SHALL be scoped to the repository's `tenant_id`.

#### Scenario: Soft delete marks deleted_at

- **WHEN** `repository.soft_delete(id)` is called
- **THEN** the record's `deleted_at` SHALL be set to a non-null timestamp

#### Scenario: Soft deleted records are excluded by default

- **WHEN** `repository.list()` is called after a record has been soft-deleted
- **THEN** the soft-deleted record SHALL NOT appear in the results

### Requirement: Escape hatches for soft delete

The repository SHALL provide `with_deleted()` and `only_deleted()` methods that return a modified repository instance with altered soft-delete behavior. These methods SHALL NOT disable the tenant scope.

#### Scenario: With_deleted includes soft-deleted records

- **WHEN** `repository.with_deleted().list()` is called
- **THEN** the results SHALL include both active and soft-deleted records
- **AND** the tenant scope SHALL still be applied

#### Scenario: Only_deleted returns only soft-deleted records

- **WHEN** `repository.only_deleted().list()` is called
- **THEN** the results SHALL include only records where `deleted_at IS NOT NULL`
- **AND** the tenant scope SHALL still be applied

### Requirement: Cross-tenant isolation guarantee

The repository SHALL prevent any query from returning data belonging to a different tenant. This SHALL be verified by test.

#### Scenario: Tenant A cannot see Tenant B data

- **WHEN** repository for Tenant A calls `.list()`
- **THEN** no records belonging to Tenant B SHALL be returned, even if they exist in the database
