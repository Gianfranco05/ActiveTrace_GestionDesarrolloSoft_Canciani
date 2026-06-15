## Why

C-10 delivered grade import (Calificacion model), threshold configuration (UmbralMateria), and completion report detection — the data foundation. But the system can't yet answer the questions that matter: WHO is at risk, WHICH activities are being passed, WHAT does the class look like at a glance. C-11 builds analytical views on top of C-10's data: at-risk detection (F2.2), ranking (F2.3), quick reports (F2.4), final grades (F2.5), TPs-uncorrected export (F2.6), and three monitoring dashboards (F2.7–F2.9). These are the features that turn raw grades into actionable intelligence for teachers, tutors, and coordinators.

## What Changes

- **Alumnos atrasados service** — query that computes which students are "atrasados" per materia×cohorte: those with missing activities OR grade < umbral (RN-06). Pure query on Calificacion + UmbralMateria + EntradaPadron, no new DB tables.
- **Ranking de actividades aprobadas** — sorted list of students by approved activity count. Only includes students with ≥1 approved activity (RN-09). Plus final grade aggregation (F2.5) grouped per student from all calificaciones.
- **Reportes rápidos per materia** — aggregated stats: total students, approved %, at-risk %, activity completion rates (F2.4).
- **Exportar TPs sin corregir** — CSV export of students who submitted textual-scale TPs that haven't been graded yet (RN-07, RN-08). Consumes existing Calificacion data, no need for completion report re-upload.
- **Monitor general** — cross-materia view for COORDINADOR/ADMIN showing all students and activity status across the tenant (F2.7).
- **Monitor seguimiento tutor/profesor** — per-materia filtered view scoped to the user's asignaciones (F2.8).
- **Monitor coordinación/admin** — full view with date range filters, cross-materia (F2.9).
- **8 new API endpoints** under `/api/analisis/` — all guarded by `atrasados:ver` permission.
- **No new DB models** — all computations are queries + derived data on Calificacion, UmbralMateria, EntradaPadron, VersionPadron.

### Key domain rules
- **RN-06**: Atrasado = missing activity OR (submitted AND grade < umbral)
- **RN-07**: TP sin corregir = submitted but no grade (null nota_numerica AND null nota_textual)
- **RN-08**: Only textual-scale activities can be "sin corregir" — numeric activities without grade = not submitted
- **RN-09**: Ranking excludes students with 0 approved activities
- All analysis is scoped by `(materia_id, cohorte_id)` — standard tenancy applies

## Capabilities

### New Capabilities
- `atrasados`: Cómputo de alumnos atrasados (F2.2, RN-06) — query-based detection per materia×cohorte
- `ranking`: Ranking de actividades aprobadas (F2.3, RN-09) + notas finales agrupadas (F2.5)
- `reportes-materia`: Reportes rápidos por materia (F2.4) + export CSV de TPs sin corregir (F2.6, RN-07/08)
- `monitores`: Monitores general/seguimiento/coordinación (F2.7, F2.8, F2.9)

### Modified Capabilities
- `backend/app/core/audit_codes.py` — add new audit codes for analysis queries (optional observability)
- `backend/app/services/__init__.py` — export new analysis services
- `backend/app/api/v1/routers/__init__.py` — register analisis router

## Impact

- **New services**: `backend/app/services/analisis/atrasados_service.py`, `analisis/ranking_service.py`, `analisis/reportes_service.py`, `analisis/monitores_service.py`
- **New router**: `backend/app/api/v1/routers/analisis.py` — 8 endpoints under `/api/analisis/`
- **New schemas**: `backend/app/schemas/analisis.py` — all response DTOs
- **Dependencies**: C-10 (Calificacion + UmbralMateria models), C-06 (Materia, Cohorte), C-07 (Usuario, Asignacion), C-09 (VersionPadron, EntradaPadron), C-04 (RBAC — `atrasados:ver` permission required)
- **Permission needed**: `atrasados:ver` — must be seeded in the permiso catalog
