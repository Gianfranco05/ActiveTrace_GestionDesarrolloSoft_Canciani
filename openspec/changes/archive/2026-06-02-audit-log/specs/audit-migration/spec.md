## ADDED Requirements

### Requirement: Migration 004 creates audit_log table
The system SHALL provide Alembic migration `004_audit_log.py` that:
1. Creates the `audit_log` table with columns: id (UUID PK), tenant_id (UUID FK), fecha_hora (DateTime), actor_id (UUID FK), impersonado_id (UUID FK nullable), materia_id (UUID nullable), accion (String 50), detalle (JSONB nullable), filas_afectadas (Integer default 0), ip (String 45 nullable), user_agent (String 500 nullable), created_at (DateTime server default)
2. Creates indexes on `(tenant_id, fecha_hora DESC)`, `(tenant_id, accion)`, `(tenant_id, actor_id)`
3. Creates the `reject_audit_log_mods()` trigger function that raises an exception
4. Creates BEFORE UPDATE and BEFORE DELETE triggers on `audit_log` using the function

The migration SHALL be additive (no destructive changes to previous migrations).

#### Scenario: Migration upgrades cleanly
- **WHEN** running `alembic upgrade head`
- **THEN** the audit_log table SHALL exist with all columns, indexes, trigger function, and triggers

#### Scenario: Migration downgrades cleanly
- **WHEN** running `alembic downgrade -1`
- **THEN** the audit_log table SHALL be removed along with the trigger function

#### Scenario: Seed data for auditoria:ver permission
- **WHEN** running the migration
- **THEN** the migration SHALL ensure that the `auditoria:ver` permission exists (idempotent via NOT EXISTS)
