## Why

C-04 established fine-grained authorization (`require_permission`) but there is no mechanism to record **what actually happened** in the system. The product name is *trace* — every meaningful action must be audited. C-05 delivers the append-only audit log (E-AUD from the KB) that all domain changes (C-06 onwards) will use to record their operations. Without C-05, there is no traceability, no impersonation audit trail, and no way to answer "who did what and when."

## What Changes

- **AuditLog ORM model** — append-only: no update, no delete at app and DB level (PostgreSQL trigger rejects UPDATE/DELETE)
- **AuditAction enum** — standardized action codes (`CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, etc.)
- **AuditLogRepository** — only `create()`, `list()`, `find_by_id()`; NO update/delete methods
- **AuditService** — service that creates audit entries with current context (actor, tenant, IP, user_agent)
- **Audit schemas** — Pydantic response schemas for audit log queries
- **Audit query router** — `GET /api/v1/audit` with filtering by action, actor, date range; protected by `require_permission("auditoria:ver")`
- **Alembic migration 004** — creates `audit_log` table + append-only trigger
- **Impersonation field** — `impersonado_id` modeled (FK → AuthUser, nullable); impersonation flow comes later

## Capabilities

### New Capabilities
- `audit-model`: AuditLog ORM model with append-only enforcement
- `audit-codes`: AuditAction enum with standardized action codes
- `audit-repository`: AuditLogRepository (create/query only, no update/delete)
- `audit-service`: AuditService for creating log entries with current context
- `audit-query-api`: GET /api/v1/audit endpoints for querying audit logs, protected by `auditoria:ver`
- `audit-migration`: Alembic migration 004 with append-only PostgreSQL trigger

### Modified Capabilities
- *(none — first audit capability)*

## Impact

- **New models**: `backend/app/models/audit_log.py` (does NOT extend BaseModelMixin — append-only, no soft delete)
- **New enum**: `backend/app/core/audit_codes.py` — `AuditAction(str, Enum)`
- **New repository**: `backend/app/repositories/audit_repository.py`
- **New service**: `backend/app/services/audit_service.py`
- **New schemas**: `backend/app/schemas/audit.py`
- **New router**: `backend/app/api/v1/routers/audit.py` (registered in main.py)
- **New migration**: `backend/alembic/versions/004_audit_log.py` + append-only trigger
- **Dependencies**: `C-04` (uses `require_permission("auditoria:ver")`), `C-03` (references `AuthUser` model)
