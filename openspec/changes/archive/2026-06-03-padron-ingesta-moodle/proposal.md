## Why

C-07 delivered Usuario (people layer) and Asignacion (role assignments). C-06 delivered Materia and Cohorte (academic structure). But neither C-06 nor C-07 models **who the students are** for any given Materia×Cohorte combination. Without a versioned student roster (padrón), there's no way to import grades (C-10), track at-risk students (C-11), or send communications to enrolled students (C-23).

The KB defines E6 — VersionPadron + EntradaPadron — as a **versioned** roster: each import creates a new version, preserving history. The previous version is soft-deactivated (not deleted). This is critical:
- Historical accuracy: grades from C-10 reference EntradaPadron rows that must survive roster updates
- Audit trail: who imported what and when is always traceable
- Student pre-registration: EntradaPadron can exist before the student has a Usuario account (usuario_id nullable)

C-09 also introduces the **Moodle Web Services integration layer** (`integrations/moodle_ws.py`) which C-10 (calificaciones) and potentially C-11 (atrasados) will extend. For C-09, the Moodle WS client only needs one method: fetch enrolled students.

## What Changes

- **VersionPadron ORM model** — versioned roster header. One active version per (materia_id, cohorte_id, tenant_id). Activating a new version deactivates the previous one. Extends BaseModelMixin (UUID PK, tenant_id, timestamps, soft delete).
- **EntradaPadron ORM model** — individual student entries under a version. Email encrypted with EncryptedString (reused from C-07). usuario_id nullable for students without accounts. nombre/apellidos denormalized for historical accuracy.
- **PadronRepository** — both models under one repository (they're intrinsically coupled). Methods: create_version, create_entries, get_active_version, deactivate_previous, get_entries, vaciar_entries.
- **File parser** — parse `.xlsx` and `.csv` files into preview rows. Headers: nombre, apellidos, email, comision, regional. Preview returns first N rows with column mapping.
- **Moodle WS client** — `integrations/moodle_ws.py` with `get_enrolled_users(materia_id, cohorte_id)` method. Mockable for tests. Fallback to manual import when Moodle is unavailable.
- **Import service** — two-phase import: parse → preview (no write) → confirm (write). On confirm: create VersionPadron (activa=true), deactivate previous, create EntradaPadron rows, audit log.
- **Vaciar (F1.5/RN-04)** — soft-delete all EntradaPadron for a given VersionPadron. Only allowed if version is NOT active. Audit log entry.
- **Pydantic schemas** — VersionPadronResponse, EntradaPadronResponse, EntradaPadronCreate, ImportPreviewResponse, ImportConfirmRequest.
- **Padron router** — `/api/v1/padron/*` endpoints: preview, confirm, vaciar, list versions, list entries. Guarded by `padron:cargar` and `padron:ver`.
- **Alembic migration 007** — creates `version_padron`, `entrada_padron` tables with unique partial index on active version and FK constraints.

## Capabilities

### New Capabilities
- `version-padron`: VersionPadron ORM model + versioning rules (one active per materia×cohorte)
- `entrada-padron`: EntradaPadron ORM model + nullable usuario_id + encrypted email
- `padron-repository`: Repository for both models
- `import-padron`: Two-phase import flow (parse → preview → confirm)
- `moodle-ws`: Moodle Web Services integration client
- `padron-api`: API endpoints for padrón management

### Modified Capabilities
- `backend/app/core/audit_codes.py` — PADRON_CARGAR already exists; no change needed
- `backend/app/models/__init__.py` — export VersionPadron, EntradaPadron
- `backend/app/integrations/` — add moodle_ws.py
- `backend/app/main.py` — register padron router

## Impact

- **New models**: `backend/app/models/padron.py`
- **New schemas**: `backend/app/schemas/padron.py`
- **New repository**: `backend/app/repositories/padron_repository.py`
- **New service**: `backend/app/services/padron_service.py`, `backend/app/services/file_parser.py`
- **New router**: `backend/app/api/v1/routers/padron.py`
- **New integration**: `backend/app/integrations/moodle_ws.py`
- **New migration**: `backend/alembic/versions/007_padron_ingesta_moodle.py`
- **Dependencies**: C-07 (Usuario model), C-06 (Materia, Cohorte models), C-05 (AuditService)
