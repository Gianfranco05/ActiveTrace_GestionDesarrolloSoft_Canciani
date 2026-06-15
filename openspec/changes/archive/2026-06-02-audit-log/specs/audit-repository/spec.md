## ADDED Requirements

### Requirement: AuditLogRepository
The system SHALL provide an `AuditLogRepository` class that ONLY exposes create and query methods:

- `create(db, audit_log: AuditLog) -> AuditLog` — persists a new audit log entry
- `list(db, tenant_id, *, accion=None, actor_id=None, fecha_desde=None, fecha_hasta=None, offset=0, limit=50) -> list[AuditLog]` — lists audit logs for a tenant with optional filters
- `find_by_id(db, id, tenant_id) -> AuditLog | None` — finds a single audit log by id within tenant scope

The repository SHALL NOT expose `update()`, `delete()`, or any mutation methods beyond `create()`.

#### Scenario: Create audit log entry
- **WHEN** calling `create()` with a valid AuditLog instance
- **THEN** the entry SHALL be persisted and returned with an assigned id

#### Scenario: List empty returns empty list
- **WHEN** calling `list()` for a tenant with no audit logs
- **THEN** an empty list SHALL be returned

#### Scenario: List filters by accion
- **WHEN** calling `list()` with an `accion` filter
- **THEN** only entries matching that action SHALL be returned

#### Scenario: List filters by actor_id
- **WHEN** calling `list()` with an `actor_id` filter
- **THEN** only entries from that actor SHALL be returned

#### Scenario: List filters by date range
- **WHEN** calling `list()` with `fecha_desde` and `fecha_hasta`
- **THEN** only entries within that date range SHALL be returned

#### Scenario: List respects tenant isolation
- **WHEN** calling `list()` for tenant A
- **THEN** entries from tenant B SHALL NOT be included

#### Scenario: List uses default pagination
- **WHEN** calling `list()` without offset/limit
- **THEN** offset SHALL default to 0 and limit SHALL default to 50

#### Scenario: Find by id returns matching entry
- **WHEN** calling `find_by_id()` with a valid id and tenant_id
- **THEN** the matching AuditLog SHALL be returned

#### Scenario: Find by id returns None for wrong tenant
- **WHEN** calling `find_by_id()` with an id that exists in a different tenant
- **THEN** None SHALL be returned (tenant isolation)

#### Scenario: Find by id returns None for non-existent
- **WHEN** calling `find_by_id()` with a non-existent id
- **THEN** None SHALL be returned

#### Scenario: No update or delete methods exposed
- **WHEN** inspecting AuditLogRepository methods
- **THEN** SHALL NOT contain `update` or `delete` methods
