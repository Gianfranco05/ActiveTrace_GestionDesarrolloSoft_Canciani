## Context

C-05 delivered the audit log foundation: AuditLog model with append-only enforcement, `AuditLogRepository` with basic `list()`/`count()` filtering, and a simple GET `/api/v1/audit` endpoint with pagination. C-04 seeded the `auditoria:ver` permission assigned to ADMIN, COORDINADOR, and FINANZAS roles.

C-19 builds analytical dashboards on top of this data — aggregations, time-series, and cross-table joins — that turn raw audit entries into supervision panels per F9.1, F9.2, and FL-11. This is a pure SERVICE + ROUTER change. No new DB models, no Alembic migrations. All analytics are read queries on existing AuditLog and Comunicacion tables.

Governance is **ALTO** — the audit log is a security invariant. The design must preserve append-only guarantees and scope isolation. The `(propio)` scope for COORDINADOR is critical: a coordinator must ONLY see their own activity, never another user's audit trail.

Key references:
- KB F9.1: Panel de interacciones — acciones por día, estado comunicaciones por docente, interacciones por docente×materia, últimas acciones (máx configurable, defecto 200)
- KB F9.2: Log completo de auditoría — filtros por fecha, materia, usuario, acción, IP (RN-23, RN-24)
- KB FL-11: Auditoría de actividad por docente — panel de supervisión
- KB §E-AUD: AuditLog entity with fecha_hora, actor_id, materia_id, accion, detalle, filas_afectadas, ip, user_agent
- KB §E21: Comunicacion entity with estado, materia_id, enviado_por
- KB 03_actores_y_roles §3.3: COORDINADOR sees auditoría `(propio)`, ADMIN and FINANZAS see global
- C-05 design decisions: D3 (AuditAction enum), D6 (permission context), D9 (query endpoints)
- C-11 (analisis-atrasados-reportes) design: D2 (service structure), D10 (repository queries) — similar aggregation pattern

## Goals / Non-Goals

**Goals:**
- `PanelInteraccionesService` — four aggregation methods querying AuditLog + Comunicacion:
  1. `acciones_por_dia(fecha_desde, fecha_hasta, usuario_id?)` → time-series of daily action counts
  2. `estado_comunicaciones_por_docente(fecha_desde, fecha_hasta, materia_id?)` → communication state distribution by teacher
  3. `interacciones_por_docente_materia(fecha_desde, fecha_hasta, usuario_id?)` → usage metrics by (user, materia) per action type
  4. `ultimas_acciones(limit?, fecha_desde?, fecha_hasta?, usuario_id?, materia_id?)` → recent AuditLog entries (configurable max, default 200)
- Enhanced `AuditLogRepository` with aggregation query methods (GROUP BY, COUNT, time-series)
- Auditoria router with 5+ endpoints under `/api/auditoria/`, all guarded by `auditoria:ver`
- Scope isolation: COORDINADOR sees only own `actor_id`; ADMIN/FINANZAS see all
- Pydantic schemas for all response DTOs (acciones por día, estado comunicaciones, interacciones, últimas acciones)
- ComunicacionRepository dependency for communication state queries

**Non-Goals:**
- New DB models, Alembic migrations, new tables — all queries on existing AuditLog + Comunicacion
- Frontend UI for the audit dashboard — C-19 is backend only
- Real-time streaming or WebSocket updates for the panel
- Export (CSV/PDF) of audit data — deferred
- Impersonation-aware filtering — impersonado_id is already in the model; filtering by it is a query concern
- Caching layer for aggregation queries — acceptable performance on indexed tables
- Automatic audit logging decorators (C-05 decision: services call AuditService explicitly)

## Decisions

### D1 — Service layer: single `MetricsService` class

```python
# backend/app/services/auditoria/metrics_service.py

class MetricsService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,            # for (propio) scope
        is_global_scope: bool,    # ADMIN/FINANZAS = True, COORDINADOR = False
    ): ...

    async def acciones_por_dia(self, ...) -> AccionesPorDiaResponse: ...
    async def estado_comunicaciones_por_docente(self, ...) -> EstadoComunicacionesResponse: ...
    async def interacciones_por_docente_materia(self, ...) -> InteraccionesResponse: ...
    async def ultimas_acciones(self, ...) -> UltimasAccionesResponse: ...
```

**Why a single service?** Unlike C-11's four separate services (which dealt with different domain models — Calificacion, EntradaPadron, UmbralMateria), C-19 has one source table (AuditLog) and one joined table (Comunicacion). A single service keeps aggregation coordination simple. The class receives `user_id` and `is_global_scope` at construction so every method automatically applies the correct scope.

**Alternative considered**: One service per metric (like C-11's per-capability split). Rejected — the metrics share the same dependency graph (AuditLogRepository + ComunicacionRepository), and splitting would create file proliferation without benefit.

### D2 — Scope isolation: `(propio)` at the service level

```python
def _apply_propio_scope(self, query, actor_id_field):
    if not self._is_global_scope:
        return query.where(actor_id_field == self._user_id)
    return query
```

**How it works:**
- **ADMIN / FINANZAS**: `is_global_scope = True` → all queries return data for every user in the tenant
- **COORDINADOR**: `is_global_scope = False` → queries are filtered by `actor_id = current_user.user_id`
- The scope is applied at the service level, not the router level. Every aggregation method implicitly respects scope.

**Why at the service level?** The router's only job is to parse HTTP params and call the service. Putting scope logic in the router would violate Clean Architecture (no business logic in routers). The `(propio)` scope IS business logic.

**Comunicacion table scope**: For communication state queries, the scope filters by `comunicacion.enviado_por = user_id` (since `enviado_por` is the FK to the user who triggered the send).

### D3 — Router structure

```
/api/auditoria/                          ← prefix
├── GET  /panel/acciones-por-dia          ← time-series
├── GET  /panel/estado-comunicaciones     ← comm states by teacher
├── GET  /panel/interacciones            ← usage metrics
├── GET  /panel/ultimas-acciones         ← recent entries (configurable limit)
├── GET  /log                            ← enhanced full log with filters
```

All endpoints guarded by `require_permission_return_user("auditoria:ver")`.

**Why `/panel/` and `/log` prefixes?** Separates the analytical panel (F9.1) from the raw query log (F9.2). The panel endpoints return DTOs with aggregated data; the log endpoint returns a paginated list of AuditLogResponse (extending C-05's format with additional filter options).

### D4 — Configurable max registros for últimas acciones

```python
# Default: 200 records
DEFAULT_ULTIMAS_ACCIONES_LIMIT = 200
# Max allowed: 1000 (prevents unbounded queries)
MAX_ULTIMAS_ACCIONES_LIMIT = 1000
```

The endpoint accepts an optional `limit` query parameter. If omitted, defaults to 200 (per F9.1). If provided, capped at 1000. This prevents a single request from fetching the entire audit log.

**Alternative considered**: Making the default configurable per-tenant via a settings table. Rejected for C-19 — adds complexity without immediate need. The default can be made configurable in a future change if tenants need different values.

### D5 — Aggregation queries: GROUP BY on AuditLog

**Acciones por día** (`GROUP BY DATE(fecha_hora)`):
```sql
SELECT DATE(fecha_hora) as dia, COUNT(*) as total_acciones
FROM audit_log
WHERE tenant_id = :tenant_id
  AND fecha_hora BETWEEN :desde AND :hasta
  [AND actor_id = :user_id]  -- (propio) scope
GROUP BY DATE(fecha_hora)
ORDER BY dia ASC
```

**Interacciones por docente×materia** (`GROUP BY actor_id, materia_id, accion`):
```sql
SELECT actor_id, materia_id, accion, COUNT(*) as cantidad
FROM audit_log
WHERE tenant_id = :tenant_id
  AND fecha_hora BETWEEN :desde AND :hasta
  [AND actor_id = :user_id]
GROUP BY actor_id, materia_id, accion
ORDER BY cantidad DESC
```

**Why not raw SQL via session.execute()?** SQLAlchemy 2.0's `select()` with `func.count()` and `func.date_trunc()` is sufficient for these GROUP BY queries. No need for raw SQL — the ORM can express all needed aggregations. This keeps the repository testable without needing to mock raw SQL execution.

### D6 — Comunicacion table join for communication states

The `estado_comunicaciones_por_docente` endpoint queries the `comunicacion` table (E21), not AuditLog. This is intentional — AuditLog records the fact that a communication was SENT, but `comunicacion.estado` tracks the full lifecycle (Pendiente → Enviando → Enviado/Error/Cancelado per RN-15).

```sql
SELECT c.enviado_por, c.materia_id, c.estado, COUNT(*) as cantidad
FROM comunicacion c
WHERE c.tenant_id = :tenant_id
  AND c.created_at BETWEEN :desde AND :hasta
  [AND c.materia_id = :materia_id]
  [AND c.enviado_por = :user_id]  -- (propio) scope
GROUP BY c.enviado_por, c.materia_id, c.estado
ORDER BY c.enviado_por, c.estado
```

**Dependency on C-12**: This endpoint requires the `comunicacion` table to exist. C-12 (comunicaciones-worker) creates the Comunicacion model and table. If C-12 is not yet deployed, this endpoint MUST be feature-flagged or return an empty response gracefully. C-19's proposal documents this dependency explicitly.

**Mitigation**: The `estado_comunicaciones_por_docente` endpoint checks if the Comunicacion model exists at import time. If not, it returns an empty response with a note that communication data is not yet available. This avoids a hard crash when running C-19 before C-12.

### D7 — Repository extension: aggregation methods on AuditLogRepository

```python
class AuditLogRepository:
    # ... existing methods from C-05 ...

    async def count_by_day(
        self, *, fecha_desde, fecha_hasta, actor_id=None,
    ) -> list[dict]: ...

    async def count_by_actor_materia_accion(
        self, *, fecha_desde, fecha_hasta, actor_id=None,
    ) -> list[dict]: ...
```

**Why extend the existing repository?** C-05's `AuditLogRepository` already has the tenant-scoped query pattern. Adding aggregation methods there keeps the repository as the single entry point for AuditLog queries. The MetricsService depends on AuditLogRepository, not on the session directly.

**Comunicacion queries**: The communication state query goes through an existing `ComunicacionRepository` (created in C-12) or a direct session query if the repository doesn't have the needed aggregation method yet.

### D8 — Response DTOs

```python
# acciones-por-dia
class AccionPorDia(BaseModel):
    dia: date
    total_acciones: int

class AccionesPorDiaResponse(BaseModel):
    items: list[AccionPorDia]
    desde: date
    hasta: date

# estado-comunicaciones
class EstadoPorDocente(BaseModel):
    usuario_id: UUID
    usuario_nombre: str | None  # resolved from Usuario table
    materia_id: UUID | None
    materia_nombre: str | None  # resolved from Materia table
    pendiente: int
    enviando: int
    enviado: int
    error: int
    cancelado: int

class EstadoComunicacionesResponse(BaseModel):
    items: list[EstadoPorDocente]

# interacciones
class InteraccionRow(BaseModel):
    usuario_id: UUID
    usuario_nombre: str | None
    materia_id: UUID | None
    materia_nombre: str | None
    accion: str
    cantidad: int

class InteraccionesResponse(BaseModel):
    items: list[InteraccionRow]

# ultimas-acciones (extends C-05's AuditLogResponse with resolved names)
class UltimaAccionResponse(BaseModel):
    id: UUID
    fecha_hora: datetime
    actor_id: UUID
    actor_nombre: str | None
    materia_id: UUID | None
    materia_nombre: str | None
    accion: str
    detalle: dict | None
    filas_afectadas: int
    ip: str | None
    user_agent: str | None

class UltimasAccionesResponse(BaseModel):
    items: list[UltimaAccionResponse]
    max_registros: int  # the actual limit used
```

**Name resolution**: User and materia names are resolved by joining with `auth_user` (C-03) and `materia` (C-06) tables in the query or via separate repository calls. For aggregation endpoints, names are resolved as part of the query (LEFT JOIN) to avoid N+1 queries. For `ultimas-acciones`, names can be resolved via a single batch query after fetching the logs.

### D9 — Permission guard pattern

Every endpoint uses the existing `require_permission_return_user("auditoria:ver")` guard from C-04. The router receives the `UserSession` and passes it to the `MetricsService` constructor:

```python
@router.get("/panel/acciones-por-dia")
async def acciones_por_dia(
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    current_user: UserSession = Depends(require_permission_return_user("auditoria:ver")),
    db: AsyncSession = Depends(get_db),
):
    service = MetricsService(
        session=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        is_global_scope="COORDINADOR" not in current_user.roles,
    )
    return await service.acciones_por_dia(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
```

**Is `is_global_scope` derived from roles or from RBAC permissions?** The KB defines `(propio)` as a property of the role, not a separate permission. A COORDINADOR has `auditoria:ver` but with `(propio)` scope. ADMIN and FINANZAS have `auditoria:ver` with global scope. Therefore, `is_global_scope` is derived from the user's roles: if the user has ADMIN or FINANZAS role, scope is global; otherwise (COORDINADOR), scope is `(propio)`.

**⚠️ TODO**: The current implementation derives `is_global_scope` from hardcoded role names (`"COORDINADOR" not in current_user.roles`). This is a known limitation. When the RBAC system supports scope attributes on permissions, this should be refactored to query `permiso.scope` instead of checking role names. For C-19, the hardcoded approach matches the KB matrix exactly and is sufficient.

### D10 — Log completo endpoint extension of C-05

The existing `GET /api/v1/audit` endpoint (C-05) already provides paginated list with `accion`, `actor_id`, `fecha_desde`, `fecha_hasta` filters. C-19 enhances this by adding:

| New filter | Type | Description |
|------------|------|-------------|
| `materia_id` | UUID | Filter by materia |
| `usuario_id` | UUID | Filter by actor (renamed from `actor_id` for API consistency) |
| `ip` | str | Filter by IP address (partial match) |

The new endpoint lives at `/api/auditoria/log` (not replacing C-05's `/api/v1/audit` — both can coexist during transition). The response format is the same `AuditLogListResponse` from C-05 plus actor name resolution.

**Why a new endpoint instead of modifying C-05's?** C-05's GET `/api/v1/audit` is a foundation endpoint used by other parts of the system. Modifying its contract could break existing consumers. C-19 adds an enhanced endpoint under the new `/api/auditoria/` prefix that can eventually replace C-05's once all consumers migrate.

## Risks / Trade-offs

- **[COORDINADOR (propio) scope depends on role-name check]** → If role names change or a custom role with `auditoria:ver` is created, the scope derivation might not match expectations. Mitigation: document the behavior clearly; future RBAC enhancement can model `scope` as a permission attribute.
- **[C-12 dependency for Comunicacion queries]** → `estado_comunicaciones_por_docente` needs the `comunicacion` table. If C-19 is applied before C-12, that endpoint returns an empty response gracefully. Mitigation: feature-flagged import; `try/except ImportError` on Comunicacion model.
- **[AuditLog table can grow large]** → Aggregation queries with GROUP BY on unbounded date ranges could become slow. Mitigation: C-19 endpoints enforce a date range (default: last 30 days if not specified) and the `ultimas_acciones` endpoint caps at 1000 rows. Index `ix_audit_log_tenant_fecha` (tenant_id, fecha_hora DESC) already exists from C-05.
- **[Name resolution via LEFT JOIN adds query complexity]** → User and materia names come from auth_user (C-03) and materia (C-06) tables. If those join queries are slow, names can be resolved in a separate batch query. For C-19, LEFT JOIN is used for aggregation endpoints (where GROUP BY already dictates the query shape) and a batch query for `ultimas_acciones`.
- **[Dual audit endpoints during transition]** → Having both `/api/v1/audit` and `/api/auditoria/log` could cause confusion. Mitigation: document the relationship; C-19's `/api/auditoria/log` is the enhanced version. C-05's endpoint can be deprecated in a future change.

## Open Questions

- **¿Debe el `(propio)` scope modelarse como atributo RBAC o inferirse del rol?** Resuelto para C-19: se infiere del rol. Si se necesitan custom roles con distintos scopes, se modela en el RBAC más adelante.
- **¿El default de 200 registros debe ser configurable por tenant?** Resuelto para C-19: no. Es constante del sistema. Si un tenant necesita otro valor, se parametriza en un change futuro.
- **¿Debe haber un endpoint de exportación CSV del log?** No en C-19. El foco es el panel de métricas. Export queda para un change futuro.
