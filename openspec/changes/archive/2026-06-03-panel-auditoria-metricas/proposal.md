## Why

C-05 delivered the foundation — AuditLog model, append-only storage, and basic list/filter API. But ADMIN and COORDINADOR need to *visualize* the audit data, not just query raw rows. The system must expose aggregated metrics — actions per day, communication status by teacher, interactions per teacher×materia, and a configurable recent-actions log — to turn the raw audit trail into actionable supervision (F9.1, F9.2, FL-11). `auditoria:ver` is already seeded by C-04; now we build the analytics that consume it.

## What Changes

- **Panel de interacciones (F9.1)**: four aggregation endpoints that query AuditLog and Comunicacion tables:
  - `acciones-por-dia`: time series of action counts grouped by day, filterable by date range and user.
  - `estado-comunicaciones-por-docente`: distribution of communication states (Pendiente/Enviando/Enviado/Error/Cancelado) aggregated by teacher.
  - `interacciones-por-docente-materia`: usage metrics by (user, materia) — counts per action type.
  - `ultimas-acciones`: recent AuditLog entries, limited by a configurable `max_registros` parameter (default 200).
- **Log completo de auditoría (F9.2)**: enhanced list endpoint with filters: `fecha_desde`, `fecha_hasta`, `materia_id`, `usuario_id`, `accion`, `ip`. Paginated, sorted by `fecha_hora DESC`.
- **Scope `(propio)` for COORDINADOR**: endpoints scope results to the user's own `actor_id` when the caller lacks the global scope (COORDINADOR sees only their own activity; ADMIN/FINANZAS see all).
- **New router** `/api/auditoria/*` with guard `auditoria:ver` on every endpoint.
- **No new DB models** — all computations are read queries and aggregations on existing AuditLog and Comunicacion tables.

## Capabilities

### New Capabilities
- `panel-interacciones`: Aggregated audit metrics — acciones por día, estado de comunicaciones por docente, interacciones por docente×materia, últimas acciones (F9.1). Read-only queries on AuditLog + Comunicacion.
- `log-completo-auditoria`: Full audit log with rich filters — date range, materia, user, action, IP (F9.2, RN-23/24). Extends C-05's audit list endpoint.

### Modified Capabilities
<!-- None — this is a new analytical layer on top of C-05. No existing spec requirements change. -->

## Impact

- **New router**: `backend/app/api/v1/routers/auditoria.py` — 5+ endpoints under `/api/auditoria/`
- **New service**: `backend/app/services/auditoria/metrics_service.py` — aggregation logic
- **New schemas**: `backend/app/schemas/auditoria.py` — response DTOs for metrics
- **Modified**: `backend/app/repositories/audit_repository.py` — add aggregation query methods
- **Dependencies**: C-05 (AuditLog model, repository, audit codes), C-04 (RBAC — `auditoria:ver` already seeded), C-07 (Usuario model for user resolution), C-12 (Comunicacion model for communication state queries)
- **Permission**: `auditoria:ver` — already in the permiso catalog (C-04 seed). No new permission needed.
