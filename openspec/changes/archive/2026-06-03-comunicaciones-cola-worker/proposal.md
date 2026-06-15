## Why

C-11 delivered analytical views (at-risk detection, ranking, monitors) — now the system can identify WHO is falling behind. But it can't yet ACT on that information. Teachers export TPs to follow up manually; there's no integrated communication channel. C-12 closes the loop: adds async email dispatch with a DB-backed worker, mandatory preview (RN-16), configurable human approval per tenant (RN-17), and full state machine tracking (RN-15). This is the last change on the critical path — the final capability that turns raw academic data into actionable communication.

## What Changes

- **Comunicacion model** — new DB entity (E21): destinatario `[cifrado]`, lote_id, estado (Pendiente → Enviando → Enviado/Error/Cancelado), template_id, variables de sustitución, requiere_aprobacion, aprobado_por, tenant_id, soft-delete. Alembic migration.
- **State machine logic** in `ComunicacionService` — enforces RN-15 transitions: Pendiente → Enviando → Enviado|Error|Cancelado. No invalid jumps.
- **Worker asíncrono** (`backend/workers/comunicacion_worker.py`) — polls DB for Pendiente records, transitions to Enviando → Enviado/Error. Processes in batches. Template rendering with variable substitution (`{{nombre}}`, `{{apellidos}}`, `{{materia}}`, etc.).
- **POST /api/comunicaciones/preview** — Preview obligatorio antes de encolar (F3.1, RN-16). Shows recipients, rendered template, estimates. Guard: `comunicacion:enviar`.
- **POST /api/comunicaciones/enviar** — Envío masivo con cola (F3.2). Creates Comunicaciones in Pendiente state, enqueues for worker. Guard: `comunicacion:enviar`.
- **POST /api/comunicaciones/{id}/aprobar** — Human approval configurable per tenant (F3.3, RN-17). Guard: `comunicacion:aprobar`. Can approve/reject full lote or individual messages.
- **GET /api/comunicaciones** — List with filters (estado, lote_id, fechas). Guard: `comunicacion:ver`.
- **GET /api/comunicaciones/{id}** — Detail view. Guard: `comunicacion:ver`.
- **POST /api/comunicaciones/{id}/cancelar** — Cancel a lote or individual message. Guard: `comunicacion:enviar`.
- **Audit actions**: `COMUNICACION_ENVIAR`, `COMUNICACION_APROBAR`, `COMUNICACION_CANCELAR`.
- **Destinatario cifrado** with AES-256 (same pattern as Usuario PII from C-07).
- **Template system** with variables: `{{nombre}}`, `{{apellidos}}`, `{{materia}}`, `{{comision}}`, `{{fecha}}`.

### Key Business Rules
- **RN-15**: State machine: Pendiente → Enviando → Enviado|Error|Cancelado. No invalid transitions.
- **RN-16**: Preview is MANDATORY before enqueuing. Shows rendered template for each recipient.
- **RN-17**: Approval configurable per tenant. Some tenants require approval, others don't.

## Capabilities

### New Capabilities
- `comunicacion-model`: Comunicacion entity + state machine + encrypted recipient + Alembic migration
- `comunicacion-preview-envio`: Preview (F3.1) + mass enqueue (F3.2) endpoints with template rendering
- `comunicacion-worker`: Async worker dispatch — polls DB, transitions Pendiente→Enviado/Error, batch processing
- `comunicacion-aprobacion`: Human approval flow (F3.3, RN-17) — configurable per tenant, approve/reject lote or individual

### Modified Capabilities
- *(none — this is the first communication capability)*

## Impact

- **New model**: `backend/app/models/comunicacion.py` — Comunicacion ORM model with soft-delete
- **New migration**: Alembic `Migración 0NN: comunicacion`
- **New service**: `backend/app/services/comunicacion_service.py` — state machine, preview, enqueue, approve, cancel
- **New worker**: `backend/app/workers/comunicacion_worker.py` — polling loop, batch dispatch
- **New schemas**: `backend/app/schemas/comunicacion.py` — request/response DTOs for all endpoints
- **New router**: `backend/app/api/v1/routers/comunicaciones.py` — 6 endpoints under `/api/comunicaciones/`
- **Permissions needed**: `comunicacion:enviar`, `comunicacion:aprobar`, `comunicacion:ver`
- **Audit codes**: `COMUNICACION_ENVIAR`, `COMUNICACION_APROBAR`, `COMUNICACION_CANCELAR`
- **Dependencies**: C-11 (atrasados analysis — who to send to), C-04 (RBAC — permission guards), C-02 (tenant isolation, soft-delete, AES-256), C-06 (Materia), C-07 (Usuario)
