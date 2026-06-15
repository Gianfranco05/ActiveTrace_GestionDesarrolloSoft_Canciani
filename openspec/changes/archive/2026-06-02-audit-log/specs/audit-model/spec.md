## ADDED Requirements

### Requirement: AuditLog ORM model
The system SHALL define an AuditLog ORM model with `__tablename__ = "audit_log"`. The model SHALL NOT extend BaseModelMixin. Fields:

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK, default uuid4 |
| `tenant_id` | UUID | FK → Tenant(id), NOT NULL, indexed |
| `fecha_hora` | DateTime | NOT NULL, default `func.now()` |
| `actor_id` | UUID | FK → AuthUser(id), NOT NULL |
| `impersonado_id` | UUID | FK → AuthUser(id), nullable |
| `materia_id` | UUID | nullable (no FK constraint yet — Materia model doesn't exist) |
| `accion` | String(50) | NOT NULL |
| `detalle` | JSONB | nullable |
| `filas_afectadas` | Integer | default 0 |
| `ip` | String(45) | nullable |
| `user_agent` | String(500) | nullable |
| `created_at` | DateTime | server default `now()` |

#### Scenario: Create audit log entry with valid fields
- **WHEN** creating an AuditLog with valid tenant_id, actor_id, accion, and optional fields
- **THEN** the AuditLog SHALL have a UUID id, the provided fields, and created_at set

#### Scenario: Audit log has no updated_at or deleted_at
- **WHEN** inspecting the AuditLog model columns
- **THEN** it SHALL NOT have `updated_at` or `deleted_at` columns (append-only invariant)

#### Scenario: Audit log defaults
- **WHEN** creating an AuditLog with only required fields
- **THEN** filas_afectadas SHALL default to 0, detalle SHALL be NULL, ip SHALL be NULL, user_agent SHALL be NULL, impersonado_id SHALL be NULL, materia_id SHALL be NULL

#### Scenario: Audit log foreign keys
- **WHEN** creating an AuditLog with an invalid tenant_id or actor_id
- **THEN** an IntegrityError SHALL be raised (FK constraints enforced)

### Requirement: Append-only at DB level
The system SHALL provide a PostgreSQL trigger that rejects UPDATE and DELETE operations on the audit_log table.

#### Scenario: UPDATE on audit_log is rejected
- **WHEN** executing an UPDATE statement on the audit_log table
- **THEN** the database SHALL raise an exception and the update SHALL NOT be applied

#### Scenario: DELETE on audit_log is rejected
- **WHEN** executing a DELETE statement on the audit_log table
- **THEN** the database SHALL raise an exception and the delete SHALL NOT be applied

#### Scenario: INSERT on audit_log succeeds
- **WHEN** executing an INSERT statement on the audit_log table
- **THEN** the insert SHALL succeed (append-only allows writes)
