## ADDED Requirements

### Requirement: Alembic async configuration

The Alembic environment SHALL be configured for asynchronous database operations using an `AsyncEngine` from SQLAlchemy's async support, compatible with `asyncpg`.

#### Scenario: Alembic env uses async engine

- **WHEN** `alembic env.py` is inspected
- **THEN** it SHALL use `run_async()` to execute migration operations asynchronously

### Requirement: Migration 001 — tenant table

The first migration SHALL create the `tenant` table with all required columns: `id` (UUID PK), `name` (string, unique, not null), `slug` (string, unique, not null, indexed), `is_active` (boolean, default True), `created_at` (datetime, not null), `updated_at` (datetime, not null).

#### Scenario: Tenant table exists after upgrade

- **WHEN** migration 001 is applied with `alembic upgrade head`
- **THEN** a `tenant` table SHALL exist in the database with the columns: id, name, slug, is_active, created_at, updated_at

#### Scenario: Tenant table is removed on downgrade

- **WHEN** migration 001 is rolled back with `alembic downgrade -1`
- **THEN** the `tenant` table SHALL NOT exist in the database

### Requirement: Seed tenant on migration

The migration 001 SHALL include a data migration step that inserts a default tenant record with `slug = "default"` and `name = "Default Tenant"`.

#### Scenario: Default tenant seeded

- **WHEN** migration 001 is applied
- **THEN** the tenant table SHALL contain a record with `slug = "default"`

#### Scenario: Default tenant removed on downgrade

- **WHEN** migration 001 is rolled back
- **THEN** the default tenant record SHALL be removed along with the table
