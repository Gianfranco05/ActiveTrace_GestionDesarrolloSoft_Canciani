## Context

C-04 delivered the authorization layer with `require_permission("auditoria:ver")`. C-05 builds the audit log foundation that every domain change (C-06 onwards) will use to record operations. The KB defines E-AUD as an append-only, immutable log of all significant actions.

The design follows KB §E-AUD, RN-23, and RN-24. Governance is **CRITICO** — audit log integrity is a security invariant.

## Goals / Non-Goals

**Goals:**
- AuditLog ORM model with fields per E-AUD
- Append-only enforcement at app level (Repository) and DB level (PostgreSQL trigger)
- AuditAction enum with initial codes from KB
- AuditService that creates log entries with current context
- Audit query endpoints (list/filter) protected by `auditoria:ver`
- Alembic migration 004 with `audit_log` table + trigger
- Impersonation field modeled (impersonado_id FK → AuthUser, nullable)

**Non-Goals:**
- Decorator/middleware for automatic audit logging — individual services call AuditService directly
- Impersonation session management — just model the field; flow comes later
- Audit dashboard UI — C-19 (panel-auditoria-metricas)
- Export/pagination beyond basic filtering — keep it simple

## Decisions

### D1 — Actor reference: FK to AuthUser (C-03), not Usuario (C-07)

`actor_id` is a FK to `AuthUser` from C-03 because the full `Usuario` model (C-07) does not exist yet. When C-07 creates Usuario with 1:1 to AuthUser, the audit log `actor_id` will still work as a FK to AuthUser. Migration C-07 can add the Usuario relationship later if needed.

### D2 — No BaseModelMixin

AuditLog is append-only — no soft delete, no update. It does NOT extend `BaseModelMixin`. Instead:
- `id`: UUID PK with default uuid4
- `tenant_id`: FK → Tenant
- `created_at` via `server_default=func.now()` (no updated_at, no deleted_at)
- Fields per E-AUD

Model uses `MappedAsDataclass` or plain `declarative_base()` with `__tablename__ = "audit_log"`.

### D3 — AuditAction enum

```python
class AuditAction(str, Enum):
    CALIFICACIONES_IMPORTAR = "CALIFICACIONES_IMPORTAR"
    PADRON_CARGAR = "PADRON_CARGAR"
    COMUNICACION_ENVIAR = "COMUNICACION_ENVIAR"
    ASIGNACION_MODIFICAR = "ASIGNACION_MODIFICAR"
    LIQUIDACION_CERRAR = "LIQUIDACION_CERRAR"
    IMPERSONACION_INICIAR = "IMPERSONACION_INICIAR"
    IMPERSONACION_FINALIZAR = "IMPERSONACION_FINALIZAR"
```

Extensible — more codes added as domain changes introduce them (RN-24).

### D4 — AuditService

```python
class AuditService:
    async def log(
        self,
        accion: AuditAction,
        actor_id: UUID,
        tenant_id: UUID,
        detalle: dict | None = None,
        filas_afectadas: int = 0,
        impersonado_id: UUID | None = None,
        materia_id: UUID | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog: ...
```

A simple service method — not over-engineered. Domain services call `AuditService.log()` when they perform significant actions. Decorators or middleware can be added in C-19 if needed.

### D5 — Append-only enforcement: two layers

**App layer**: `AuditLogRepository` exposes ONLY `create()`, `list()`, and `find_by_id()`. No `update()`, no `delete()`, no `soft_delete()`. The method signatures make it impossible to modify audit records from the app.

**DB layer**: A PostgreSQL trigger function `reject_audit_log_mods()` is created in migration 004 that raises an exception on UPDATE or DELETE of the `audit_log` table. This ensures append-only even if someone bypasses the app.

### D6 — Permission context

Query endpoints are protected by `require_permission("auditoria:ver")` (from C-04 seed). The guard prevents unauthorized access at the router level. No permission check on `log()` — AuditService is called by OTHER authenticated services; authorization is the caller's responsibility.

### D7 — Impersonation field only

C-05 models `impersonado_id` as a nullable FK → AuthUser. The actual impersonation flow (session management, visual indicators, start/end endpoints) comes later. For C-05, we just capture `impersonado_id` when it's provided.

### D8 — AuditLog model fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK, default uuid4 |
| `tenant_id` | UUID | FK → Tenant(id), NOT NULL, indexed |
| `fecha_hora` | DateTime | NOT NULL, default `func.now()` |
| `actor_id` | UUID | FK → AuthUser(id), NOT NULL |
| `impersonado_id` | UUID | FK → AuthUser(id), nullable |
| `materia_id` | UUID | nullable (future FK → Materia) |
| `accion` | String(50) | NOT NULL, AuditAction code |
| `detalle` | JSONB | nullable |
| `filas_afectadas` | Integer | default 0 |
| `ip` | String(45) | nullable, IPv4/IPv6 |
| `user_agent` | String(500) | nullable |
| `created_at` | DateTime | server default `now()` |

Indexes:
- `(tenant_id, fecha_hora DESC)` — common query pattern
- `(tenant_id, accion)` — filter by action
- `(tenant_id, actor_id)` — filter by actor

### D9 — Query endpoints

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/api/v1/audit` | `auditoria:ver` | List audit logs, filterable by `accion`, `actor_id`, `fecha_desde`, `fecha_hasta` |
| GET | `/api/v1/audit/{id}` | `auditoria:ver` | Get single audit log entry |

Response: paginated list of `AuditLogResponse` with id, fecha_hora, accion, actor_id, impersonado_id (nullable), materia_id (nullable), detalle, filas_afectadas, ip, user_agent.

### D10 — Alembic migration structure

Migration `004_audit_log.py`:
1. `op.create_table('audit_log', ...)` with all columns, FKs, indexes
2. Create trigger function:
   ```sql
   CREATE OR REPLACE FUNCTION reject_audit_log_mods()
   RETURNS TRIGGER AS $$
   BEGIN
       RAISE EXCEPTION 'audit_log is append-only: UPDATE/DELETE not allowed';
   END;
   $$ LANGUAGE plpgsql;
   ```
3. Create triggers:
   ```sql
   CREATE TRIGGER trg_audit_log_no_update
       BEFORE UPDATE ON audit_log
       FOR EACH ROW EXECUTE FUNCTION reject_audit_log_mods();
   CREATE TRIGGER trg_audit_log_no_delete
       BEFORE DELETE ON audit_log
       FOR EACH ROW EXECUTE FUNCTION reject_audit_log_mods();
   ```
4. Downgrade: drop triggers, drop function, drop table

## Risks / Trade-offs

- **[No automatic audit decorator]** → Services must explicitly call AuditService.log(). Trade-off: simpler, less magic. If we find every service duplicates the same pattern, a decorator can be layered in C-19.
- **[FK to AuthUser instead of Usuario]** → When C-07 creates Usuario, we may need a migration to add a direct relationship. However, actor_id FK to AuthUser remains valid and correct.
- **[No retention policy]** → Audit log grows unbounded. TBD later (C-19 or ops concern). For now, `auditoria:ver` is ADMIN-only, limiting who can query.

## Migration Plan

1. Implement AuditAction enum in `core/audit_codes.py`
2. Implement AuditLog model in `models/audit_log.py` (does NOT extend BaseModelMixin)
3. Update `models/__init__.py` to export AuditLog
4. Implement AuditLog schemas in `schemas/audit.py`
5. Implement AuditLogRepository in `repositories/audit_repository.py` (create/query only)
6. Implement AuditService in `services/audit_service.py`
7. Implement audit router in `api/v1/routers/audit.py` + register in main.py
8. Generate Alembic migration 004 (create table + append-only trigger)
9. Write tests per spec (TDD: RED → GREEN → TRIANGULATE)
10. Run full test suite
11. Verify lint + type-check

## Open Questions

- **¿Debemos agregar paginación con cursor o page/offset?** Decisión: offset-based pagination (simpler, adequate for ADMIN-only queries). Cursor-based can be added later if the table grows large.
- **¿Los códigos de acción deberían ser configurables por tenant?** Decisión: no — el catálogo es global y se extiende vía código (RN-24). Un tenant no puede inventar sus propios códigos.
