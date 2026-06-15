## Why

C-09 delivered the versioned student roster (VersionPadron + EntradaPadron) — the data backbone for grade tracking. But without the Calificacion model and UmbralMateria configuration, the system cannot ingest grades from Moodle exports, determine which students passed each activity, or detect at-risk students. C-10 is the next step in the critical path: it enables importación de calificaciones (F1.1), reporte de finalización (F1.2), and umbral configuration (F2.1), which together unlock C-11 (análisis de atrasados) and C-12 (comunicaciones).

The KB defines E7 (Calificacion with derived aprobado) and E8 (UmbralMateria with default 60% threshold). The derived aprobado field is critical: it must be computed at import time based on the active umbral, and modifying the umbral later must NOT retroactively change existing grades.

## What Changes

- **Calificacion ORM model** — per-alumno grade entry: materia_id, cohorte_id, entrada_padron_id (FK → EntradaPadron), actividad (string), tipo (Numerica/Textual), nota_numerica (nullable Decimal), nota_textual (nullable Text), aprobado (derived boolean), origen (Importado/Manual), importado_at. Extends BaseModelMixin.
- **UmbralMateria ORM model** — threshold configuration per materia: materia_id, asignacion_id (FK → Asignacion), umbral_pct (default 60), valores_aprobatorios (list of strings). One active per materia.
- **CalificacionRepository** — create, bulk-create, query by materia+cohorte, query by entrada_padron_id.
- **UmbralRepository** — get for materia, upsert.
- **File parser extension** — detect numeric vs textual activity columns in grade files. Numeric columns end with `(Real)` (RN-01). Textual columns are everything else (actividad name).
- **Import grade service** — three-phase flow: preview (upload + detect activities) → confirm (create Calificacion records, derive aprobado from current umbral) → reporte-finalizacion (detect TPs entregados sin nota, F1.2).
- **Umbral service** — get current umbral for materia, set/update umbral (validates 1–100 range, default 60%).
- **Pydantic schemas** — CalificacionResponse, CalificacionCreate, UmbralResponse, UmbralUpdate, ImportPreviewResponse, ImportConfirmRequest, ReporteFinalizacionResponse.
- **Calificaciones router** — `/api/calificaciones/*` endpoints: import preview, import confirm, reporte-finalizacion, get/set umbral.
- **Alembic migration 008** — creates `calificacion`, `umbral_materia` tables.

### Key domain rules
- **Calificacion.aprobado is DERIVED**: if Numerica, compare nota_numerica >= umbral_pct; if Textual, check nota_textual is in valores_aprobatorios set
- **Umbral changes do NOT retroactively affect existing grades** — aprobado is computed at import time with current umbral
- **RN-04 scope isolation**: grade import is scoped to (usuario_id, materia_id) — other teachers' imports are unaffected
- **RN-07/RN-08**: reporte-finalizacion cross-references completion data with existing grades, only flagging textual-scale activities as "posibles sin corregir"

## Capabilities

### New Capabilities
- `calificacion-model`: Calificacion + UmbralMateria ORM models, derived aprobado, FK relationships
- `calificacion-repository`: Repository for Calificacion (bulk create, query by materia/cohorte)
- `umbral-repository`: Repository for UmbralMateria (get, upsert)
- `importar-calificaciones`: Two-phase import (preview → confirm) + activity column detection (numeric vs textual)
- `reporte-finalizacion`: Completion report import (F1.2) — detect TPs entregados sin nota
- `umbral-materia`: Umbral configuration (F2.1) — get/set with validation
- `calificaciones-api`: API endpoints for grade import and umbral configuration

### Modified Capabilities
- `backend/app/core/audit_codes.py` — CALIFICACIONES_IMPORTAR already exists, no change needed
- `backend/app/models/__init__.py` — export Calificacion, UmbralMateria
- `backend/app/main.py` — register calificaciones router
- `backend/app/services/file_parser.py` — extend with numeric/textual activity column detection (if reused; otherwise new parser)

## Impact

- **New models**: `backend/app/models/calificacion.py`
- **New schemas**: `backend/app/schemas/calificacion.py`
- **New repositories**: `backend/app/repositories/calificacion_repository.py`, `backend/app/repositories/umbral_repository.py`
- **New services**: `backend/app/services/calificacion_service.py`, `backend/app/services/umbral_service.py`
- **New router**: `backend/app/api/v1/routers/calificaciones.py`
- **New migration**: `backend/alembic/versions/008_calificaciones_y_umbral.py`
- **Dependencies**: C-09 (EntradaPadron model), C-06 (Materia, Cohorte models), C-07 (Usuario, Asignacion models), C-05 (AuditService)
