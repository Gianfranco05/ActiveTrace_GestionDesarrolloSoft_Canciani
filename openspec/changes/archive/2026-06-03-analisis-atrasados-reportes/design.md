## Context

C-10 delivered the grade data foundation (Calificacion model, UmbralMateria, grade import flow). The system now stores per-student grades with derived `aprobado` booleans and per-materia thresholds. C-11 builds analytical views on top of this data — at-risk detection, ranking, reports, and monitors — that turn raw grades into actionable intelligence for teachers, tutors, and coordinators (F2.2–F2.9).

This is a pure SERVICE + ROUTER change. No new DB models, no Alembic migrations, no new repositories. All analytics are query-based on existing Calificacion + UmbralMateria + EntradaPadron + VersionPadron tables. The KB defines the business rules (RN-06 through RN-09) and the user stories (F2.2 through F2.9).

Governance is **MEDIO** — standard domain logic queries, no security invariants, no auth flow modification. All endpoints guarded by the `atrasados:ver` permission.

Key references:
- KB F2.2: Alumnos atrasados — missing activity OR grade < umbral (RN-06)
- KB F2.3: Ranking de actividades aprobadas — sorted by approval count, excludes 0 approved (RN-09)
- KB F2.4: Reportes rápidos por materia — aggregated stats
- KB F2.5: Notas finales agrupadas — per-student final grade from all calificaciones
- KB F2.6: Exportar TPs sin corregir — CSV export (RN-07, RN-08)
- KB F2.7: Monitor general (COORDINADOR/ADMIN)
- KB F2.8: Monitor seguimiento (PROFESOR/TUTOR)
- KB F2.9: Monitor coordinación (COORDINADOR/ADMIN, date range)
- KB FL-02 pasos 5–6: flujo central del profesor
- RN-06, RN-07, RN-08, RN-09
- C-10 design decisions for Calificacion model structure, scope isolation, stored aprobado

## Goals / Non-Goals

**Goals:**
- `AtrasadosService` — query-based detection of at-risk students per materia×cohorte (RN-06). Returns students with missing activities OR grade < umbral.
- `RankingService` — sorted list of students by approved activity count. Excludes students with 0 approved activities (RN-09). Pure query on Calificacion.
- `NotasFinalesService` — per-student final grade aggregation grouped from all calificaciones (F2.5).
- `ReportesService` — aggregated stats per materia (F2.4): total students, approved %, at-risk %, activity completion distribution.
- `ExportService` — CSV export of TPs sin corregir (F2.6, RN-07/08). Cross-references Calificacion records where type=Textual AND (nota_numerica IS NULL AND nota_textual IS NULL).
- `MonitorGeneralService` — cross-materia view for COORDINADOR/ADMIN (F2.7). Aggregates all materias the user can see.
- `MonitorSeguimientoService` — per-materia detailed view scoped to user's asignaciones (F2.8).
- `MonitorCoordinacionService` — full view with date range filters, cross-materia (F2.9).
- Pydantic schemas for all response DTOs.
- Analisis router with 8 endpoints under `/api/analisis/`.
- Seed `atrasados:ver` permission if not auto-created.
- Audit logging for analysis queries (optional observability).

**Non-Goals:**
- New DB models, new repositories, Alembic migrations — all queries on existing tables.
- Grade import, completion report upload, umbral configuration — those are C-10 scope.
- Real-time notifications for at-risk detection — deferred to C-12 (comunicaciones).
- Frontend UI for monitors and reports — deferred to later changes.
- Per-student grade editing or manual override.
- Caching layer for aggregate queries — acceptable performance on read-replica.

## Decisions

### D1 — All analytics are query-based, no new models

Every computation in C-11 is a query on existing tables. The Calificacion model stores `aprobado` (derived at C-10 import time), so:
- **Atrasados**: query Calificacion for students with `aprobado=False` OR missing activities (students in EntradaPadron who have no Calificacion for a given actividad).
- **Ranking**: `GROUP BY entrada_padron_id` with `COUNT(*) WHERE aprobado=True`, sorted descending.
- **Notas finales**: `GROUP BY entrada_padron_id` aggregating nota_numerica (average or sum depending on materia config).
- **TPs sin corregir**: Calificacion rows where `tipo='Textual'` AND `nota_numerica IS NULL` AND `nota_textual IS NULL` — these are imported calificaciones without a grade yet.
- **Reportes**: `COUNT`, `AVG`, and ratio queries on Calificacion + EntradaPadron.
- **Monitores**: aggregate queries across materias, with role-based scope filtering.

**Why query-based?** The data is already structured and indexed (`IX on materia_id+cohorte_id`, `IX on entrada_padron_id`). Materializing derived views would add sync complexity without benefit — these are analytical queries on a snapshot of data that changes only when new grades are imported.

### D2 — Service layer structure: one service file per capability

```
backend/app/services/analisis/
├── __init__.py
├── atrasados_service.py    # F2.2 — alumnos atrasados
├── ranking_service.py      # F2.3 — ranking + F2.5 — notas finales
├── reportes_service.py     # F2.4 — reportes rápidos + F2.6 — export TPs
└── monitores_service.py    # F2.7, F2.8, F2.9 — monitors
```

Each service is a class with async methods, injected with the existing repositories it needs (CalificacionRepository, UmbralRepository, Repos for Materia, Cohorte, EntradaPadron, VersionPadron, Asignacion). No new repositories needed — all queries use existing repository methods or raw SQL via session.execute() for complex aggregations.

**Why split by capability?** Each maps 1:1 to a proposal capability and a spec file. Keeps files focused and testable. The monitor service is the largest (3 views), but each view is a single method.

### D3 — Router structure

| Method | Path | Guard | Rol scope | Description |
|--------|------|-------|-----------|-------------|
| GET | `/api/analisis/atrasados` | `atrasados:ver` | PROFESOR/TUTOR/COORDINADOR/ADMIN | Query params: materia_id, cohorte_id |
| GET | `/api/analisis/ranking` | `atrasados:ver` | PROFESOR/COORDINADOR | Query params: materia_id, cohorte_id |
| GET | `/api/analisis/reportes/materia/{materia_id}` | `atrasados:ver` | PROFESOR/COORDINADOR | Path param: materia_id |
| GET | `/api/analisis/notas-finales` | `atrasados:ver` | PROFESOR | Query params: materia_id, cohorte_id |
| GET | `/api/analisis/export/tps-sin-corregir` | `atrasados:ver` | PROFESOR/COORDINADOR | Query params: materia_id, cohorte_id; returns CSV |
| GET | `/api/analisis/monitor/general` | `atrasados:ver` | COORDINADOR/ADMIN | No required filters |
| GET | `/api/analisis/monitor/seguimiento` | `atrasados:ver` | PROFESOR/TUTOR | Query params: materia_id (optional) |
| GET | `/api/analisis/monitor/coordinacion` | `atrasados:ver` | COORDINADOR/ADMIN | Query params: desde, hasta, materia_id (optional) |

**Scope isolation pattern** (from C-10 D2):
- PROFESOR/TUTOR: queries are scoped to their own asignaciones. They only see data for materias they are assigned to.
- COORDINADOR/ADMIN: no materia-level filtering — they see everything in the tenant.
- TUTOR: same scope as PROFESOR but limited to monitor views (F2.8).

**Permission note**: `atrasados:ver` is a NEW permission that must be created in the permiso catalog and assigned to PROFESOR, TUTOR, COORDINADOR, and ADMIN roles. This follows the same pattern as C-10's `calificaciones:cargar` and `calificaciones:ver`.

### D4 — Atrasados detection algorithm (RN-06)

For a given `(materia_id, cohorte_id)`:

1. Load all EntradaPadron entries from the active VersionPadron.
2. Load all distinct `actividad` values from Calificacion for this materia×cohorte.
3. For each student entrada:
   a. Get all their Calificacion records for this materia×cohorte.
   b. Count how many distinct actividades they HAVE a grade for.
   c. If `count_actividades_con_nota < total_actividades_en_materia` → atrasado (missing activity).
   d. For each actividad they DO have: if `aprobado=False` → atrasado (grade below umbral).
4. Return deduplicated list of at-risk students with reasons (missing_actividades list, reprobadas list).

```python
@dataclass
class AlumnoAtrasado:
    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    email: str | None
    comision: str | None
    motivo: str  # "actividades_faltantes" | "nota_baja" | "ambos"
    actividades_faltantes: list[str]
    actividades_reprobadas: list[str]
```

**Edge case**: If no Calificacion records exist yet for the materia, ALL students are flagged as "atrasados por actividades_faltantes" — which is correct (no data = all at risk).

### D5 — Ranking algorithm (RN-09)

For a given `(materia_id, cohorte_id)`:

1. Query Calificacion: `SELECT entrada_padron_id, COUNT(*) as aprobadas FROM calificacion WHERE materia_id=X AND cohorte_id=Y AND aprobado=True GROUP BY entrada_padron_id HAVING COUNT(*) > 0 ORDER BY aprobadas DESC`.
2. Only students with ≥1 approved activity appear (RN-09 — HAVING COUNT(*) > 0).
3. Join with EntradaPadron to get student names.
4. Ties: alphabetical by apellidos.

```python
@dataclass
class RankingRow:
    posicion: int
    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    aprobadas: int
    total_actividades: int
    porcentaje: Decimal  # aprobadas / total_actividades * 100
```

### D6 — Notas finales aggregation (F2.5)

For a given `(materia_id, cohorte_id)`:

1. Group Calificacion by `entrada_padron_id`.
2. For numeric-type activities: aggregate using a configurable strategy. Default: average of all numeric nota_numerica values.
3. For textual activities: include in final note but as "N/A" for aggregation.
4. The aggregation strategy is materia-level config (future: could be per-materia). For C-11, simple average.

```python
@dataclass
class NotaFinalRow:
    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    nota_promedio: Decimal | None  # average of all numeric calificaciones
    actividades_aprobadas: int
    total_actividades: int
    estado: str  # "Promocionado" | "Regular" | "Libre" — future semantic
```

**Status label**: For C-11, `estado` is informational only — derived from `actividades_aprobadas >= threshold` where threshold = ceil(total_actividades * 0.6). Exact semantics deferred to implementation review.

### D7 — TPs sin corregir export (RN-07, RN-08)

For a given `(materia_id, cohorte_id)`:

1. Query Calificacion where `tipo='Textual'` AND `nota_numerica IS NULL` AND `nota_textual IS NULL` — these are imported textual activities that received a student submission (completion report) but no grade.
2. Only textual-scale activities (RN-08): numeric activities without grade = the student didn't submit, not pending review.
3. Join with EntradaPadron for student details.
4. Group by actividad for the report view.
5. CSV export: synchronous, generates in-memory CSV with columns: `actividad, alumno_nombre, alumno_apellidos, alumno_email, comision`.

```python
@dataclass
class TPSinCorregirRow:
    actividad: str
    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    email: str | None
    comision: str | None
```

**Why no re-upload?** Unlike C-10's reporte-finalizacion (which needed a new file upload to compare), C-11 already has Calificacion records stored. The detection is: imported textual activity + no grade = pending correction. The teacher already uploaded the completion report during C-10 import flow.

### D8 — Reportes rápidos schema (F2.4)

```python
@dataclass
class ReporteMateria:
    materia_id: UUID
    materia_nombre: str
    cohorte_id: UUID
    cohorte_nombre: str
    total_alumnos: int
    alumnos_con_nota: int       # have at least one Calificacion
    alumnos_aprobados: int       # students with >=1 approved activity
    alumnos_atrasados: int       # flagged by atrasados algorithm
    pct_aprobados: Decimal       # alumnos_aprobados / total_alumnos * 100
    pct_atrasados: Decimal       # alumnos_atrasados / total_alumnos * 100
    actividades_count: int       # distinct activities in this materia
    ultima_importacion: datetime | None
```

### D9 — Monitor view schemas

**Monitor general (F2.7)**:
Cross-materia aggregate. Groups reportes data across all materias the user has access to (for COORDINADOR/ADMIN = all tenant materias).

```python
@dataclass
class MonitorGeneralRow:
    materia_id: UUID
    materia_nombre: str
    cohorte_id: UUID
    cohorte_nombre: str
    total_alumnos: int
    aprobados: int
    atrasados: int
    pct_aprobacion: Decimal
```

**Monitor seguimiento (F2.8)**:
Per-materia detailed view. Shows each student's status within a single materia, filtered by user's asignacion scope.

```python
@dataclass
class MonitorSeguimientoRow:
    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    email: str | None
    comision: str | None
    actividades_aprobadas: int
    actividades_reprobadas: int
    actividades_faltantes: int
    nota_promedio: Decimal | None
    estado: str  # "Al día" | "Atrasado" | "Sin datos"
```

**Monitor coordinación (F2.9)**:
Same as MonitorGeneral but with date range filter (`desde`, `hasta`). Filters Calificacion by `importado_at` range.

### D10 — Repository queries: existing repos suffice

All analysis queries can be expressed through existing repository methods plus direct session queries for complex aggregations:

```python
# Examples of queries needed

# Atrasados — students with no Calificacion for a given actividad
SELECT e.id FROM entrada_padron e
WHERE e.version_padron_id IN (
    SELECT v.id FROM version_padron v
    WHERE v.materia_id = :materia_id AND v.cohorte_id = :cohorte_id AND v.activa = True
)
AND e.id NOT IN (
    SELECT c.entrada_padron_id FROM calificacion c
    WHERE c.materia_id = :materia_id AND c.cohorte_id = :cohorte_id AND c.actividad = :actividad
)

# Ranking — approved count per student
SELECT c.entrada_padron_id, COUNT(*) as aprobadas
FROM calificacion c
WHERE c.materia_id = :materia_id AND c.cohorte_id = :cohorte_id AND c.aprobado = True
GROUP BY c.entrada_padron_id
HAVING COUNT(*) > 0
ORDER BY aprobadas DESC

# TPs sin corregir — textual activities without any grade
SELECT c.* FROM calificacion c
WHERE c.materia_id = :materia_id
  AND c.cohorte_id = :cohorte_id
  AND c.tipo = 'Textual'
  AND c.nota_numerica IS NULL
  AND c.nota_textual IS NULL

# Notas finales — per-student average of numeric grades
SELECT c.entrada_padron_id, AVG(c.nota_numerica) as promedio
FROM calificacion c
WHERE c.materia_id = :materia_id AND c.cohorte_id = :cohorte_id
  AND c.tipo = 'Numerica' AND c.nota_numerica IS NOT NULL
GROUP BY c.entrada_padron_id
```

**No new repositories.** Each service receives existing repositories via DI and runs queries through `db_session.execute()` for aggregations.

### D11 — Audit observability

Each analysis query endpoint optionally logs an audit entry with:
- Action code: `ANALISIS_CONSULTAR_ATRASADOS`, `ANALISIS_CONSULTAR_RANKING`, etc.
- Context: materia_id, cohorte_id (where applicable)
- Actor: current user (from session)

This is passive observability — not a requirement but good practice. Implementation: inject `AuditService` into analysis services and call `log_action()` with a standardized action code enum.

```python
class AuditAction(str, enum.Enum):
    # ... existing actions from C-05 ...
    ANALISIS_ATRASADOS = "ANALISIS_ATRASADOS"
    ANALISIS_RANKING = "ANALISIS_RANKING"
    ANALISIS_REPORTE = "ANALISIS_REPORTE"
    ANALISIS_NOTAS_FINALES = "ANALISIS_NOTAS_FINALES"
    ANALISIS_EXPORT_TPS = "ANALISIS_EXPORT_TPS"
    ANALISIS_MONITOR = "ANALISIS_MONITOR"
```

### D12 — Non-functional: performance expectations

| Query type | Expected data volume | Expected performance |
|-----------|---------------------|---------------------|
| Atrasados | ≤500 students × ≤20 activities per materia | <100ms with proper indexing |
| Ranking | ≤500 students | <50ms |
| Reportes | Per-materia aggregates | <50ms |
| Notas finales | ≤500 students | <50ms |
| TPs sin corregir | ≤500 students × ≤10 textual activities | <100ms |
| Monitor general | ≤50 materias | <200ms |
| Monitor seguimiento | ≤500 students per materia | <100ms |
| Monitor coordinación | Same as general + date filter | <300ms |

**Indexes**: The existing indexes from C-10 (`IX on materia_id+cohorte_id`, `IX on entrada_padron_id`, `IX on cargado_por`) are sufficient. No new indexes needed.

## Risks / Trade-offs

- **[No caching for monitors]** → Monitor views aggregate across materias. With ≤50 materias and ≤500 students each, queries will be fast enough (<300ms). If performance degrades with scale, add a materialized view or Redis cache. Trade-off: simpler implementation without cache invalidation complexity.
- **[atrasados:ver permission seeding]** → Same risk as C-10's calificaciones:cargar and calificaciones:ver. If the permission doesn't auto-seed, a data migration or seed script must create it. Blocking issue: without the permission, all endpoints return 403.
- **[Atrasados without Calificacion data edge case]** → If a materia has an active padron but no grades imported yet, ALL students appear as atrasados. This is correct per RN-06 (missing activities = atrasado), but could be confusing if the teacher hasn't imported grades yet. Mitigation: the reportes endpoint should show "sin datos" state when no Calificacion records exist.
- **[Grade scale assumption]** → The ranking and notas finales assume grades are on a comparable scale (0-100 or percentage-based). If mixed-scale grades exist, the aggregate queries need normalization. Mitigation: document the assumption and add a validation note. If needed, a configurable grade-scale can be added later.
- **[Monitor date range impacts performance]** → The date-range filter in monitor coordinación (F2.9) adds a WHERE clause on `importado_at`. This is indexed (importado_at is a btree index by default). Acceptable.
- **[CSV export synchronous]** → For ≤500 rows, synchronous CSV generation is fine (<50ms). If the export grows, move to background task with download link.

## Migration Plan

1. Register `atrasados:ver` permission in the permiso catalog (seed script or data migration)
2. Add new audit action codes (`ANALISIS_*`) to AuditAction enum
3. Implement schemas in `backend/app/schemas/analisis.py`
4. Implement `AtrasadosService` in `backend/app/services/analisis/atrasados_service.py`
5. Implement `RankingService` + `NotasFinalesService` in `backend/app/services/analisis/ranking_service.py`
6. Implement `ReportesService` + `ExportService` in `backend/app/services/analisis/reportes_service.py`
7. Implement `MonitoresService` in `backend/app/services/analisis/monitores_service.py`
8. Implement `AnalisisRouter` in `backend/app/api/v1/routers/analisis.py` + register in main.py
9. Write tests for all services and endpoints (TDD per task)
10. Run full test suite — verify 518 passed + new tests
