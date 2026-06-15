# comunicacion-preview-envio Specification

## Purpose
TBD - created by archiving change comunicaciones-cola-worker. Update Purpose after archive.
## Requirements
### Requirement: Preview before enqueue (F3.1, RN-16)
The system SHALL require a mandatory preview call BEFORE any messages can be enqueued. The preview SHALL render the template with variables for a sample of recipients, show estimated totals, and return a `preview_token` required by the enqueue endpoint.

#### Scenario: Preview returns sample recipients
- **WHEN** the user calls POST /api/comunicaciones/preview with template_id, materia_id, cohorte_id, and recipient filter
- **THEN** the system SHALL return the first 5 recipients with their rendered `asunto` and `cuerpo`
- **AND** SHALL include a `total_estimado` count of all matching recipients
- **AND** SHALL include a `preview_token` (hex string, 16 chars)

#### Scenario: Preview renders template variables
- **WHEN** a template contains `{{nombre}}` placeholders
- **THEN** the preview SHALL substitute each variable with the corresponding student data
- **AND** the response SHALL show the resolved text, not the raw template

#### Scenario: Preview without authorization returns 403
- **WHEN** a user without the `comunicacion:enviar` permission calls POST /api/comunicaciones/preview
- **THEN** the system SHALL return 403 Forbidden

#### Scenario: Preview with invalid template_id
- **WHEN** the user provides a non-existent `template_id`
- **THEN** the system SHALL return 404 Not Found

#### Scenario: Preview logs audit event
- **WHEN** preview is executed successfully
- **THEN** the system SHALL log a `COMUNICACION_PREVIEW` audit event
- **AND** the audit detail SHALL include the materia_id, cohorte_id, and total_estimado

### Requirement: Mass enqueue with cola (F3.2)
The system SHALL support mass enqueue of communications. After mandatory preview, the enqueue endpoint creates one Comunicacion record per recipient in Pendiente state, grouped by a server-generated `lote_id`.

#### Scenario: Enqueue creates Comunicacion records
- **WHEN** the user calls POST /api/comunicaciones/enviar with a valid `preview_token`, template_id, materia_id, and cohorte_id
- **THEN** the system SHALL create one Comunicacion record per matching recipient
- **AND** each record SHALL be in 'Pendiente' state
- **AND** all records SHALL share the same `lote_id`
- **AND** the response SHALL include the `lote_id` and total `creados` count

#### Scenario: Enqueue requires valid preview_token
- **WHEN** the user calls POST /api/comunicaciones/enviar without a `preview_token`
- **THEN** the system SHALL return 400 Bad Request with error "Preview required before enqueue"

#### Scenario: Enqueue rejects expired preview_token
- **WHEN** the user calls POST /api/comunicaciones/enviar with a `preview_token` older than 15 minutes
- **THEN** the system SHALL return 400 Bad Request with error "Preview token expired"

#### Scenario: Enqueue without authorization returns 403
- **WHEN** a user without `comunicacion:enviar` calls POST /api/comunicaciones/enviar
- **THEN** the system SHALL return 403 Forbidden

#### Scenario: Enqueue logs audit event
- **WHEN** enqueue succeeds
- **THEN** the system SHALL log a `COMUNICACION_ENVIAR` audit event
- **AND** the audit detail SHALL include lote_id, materia_id, total_creados

### Requirement: List comunicaciones with filters
The system SHALL support listing Comunicacion records with optional filters: estado, lote_id, created_at range. Results SHALL be scoped to the user's tenant.

#### Scenario: List by estado
- **WHEN** the client calls GET /api/comunicaciones?estado=Pendiente
- **THEN** the system SHALL return only Comunicacion records in Pendiente state

#### Scenario: List by lote_id
- **WHEN** the client calls GET /api/comunicaciones?lote_id=<uuid>
- **THEN** the system SHALL return all records in that lote

#### Scenario: List by date range
- **WHEN** the client calls GET /api/comunicaciones?desde=2026-06-01&hasta=2026-06-30
- **THEN** the system SHALL return records where created_at falls within that range

#### Scenario: List without authentication returns 401
- **WHEN** an unauthenticated client calls GET /api/comunicaciones
- **THEN** the system SHALL return 401 Unauthorized

#### Scenario: List without authorization returns 403
- **WHEN** a user without `comunicacion:ver` calls GET /api/comunicaciones
- **THEN** the system SHALL return 403 Forbidden

#### Scenario: Scope isolation on list PROFESOR/TUTOR
- **WHEN** a PROFESOR or TUTOR calls GET /api/comunicaciones
- **THEN** the results SHALL be scoped to materias where the user has an active asignacion

### Requirement: Detail de comunicacion
The system SHALL support retrieving a single Comunicacion record by its id.

#### Scenario: Detail returns full record
- **WHEN** the client calls GET /api/comunicaciones/{id} with a valid id
- **THEN** the system SHALL return the full Comunicacion record including estado, lote_id, asunto, cuerpo (decrypted), created_at, enviado_at

#### Scenario: Detail for non-existent id returns 404
- **WHEN** the client calls GET /api/comunicaciones/{id} with an invalid id
- **THEN** the system SHALL return 404 Not Found

#### Scenario: Detail cross-tenant returns 404 (not 403)
- **WHEN** a user from tenant A calls GET /api/comunicaciones/{id} for a record from tenant B
- **THEN** the system SHALL return 404 Not Found (tenant isolation — no information leak)

### Requirement: Cancelar comunicacion
The system SHALL support canceling Comunicacion records in Pendiente state. Cancelation can be by individual id or by lote_id.

#### Scenario: Cancel by lote_id
- **WHEN** the user calls POST /api/comunicaciones/{lote_id}/cancelar with a valid lote_id
- **THEN** ALL records in that lote with estado='Pendiente' SHALL transition to 'Cancelado'

#### Scenario: Cancel by individual id
- **WHEN** the user calls POST /api/comunicaciones/{id}/cancelar with a valid Comunicacion id
- **THEN** that specific record SHALL transition to 'Cancelado' (if in Pendiente state)

#### Scenario: Cancel ignores non-Pendiente records
- **WHEN** canceling by lote_id
- **THEN** records in 'Enviando', 'Enviado', or 'Error' state SHALL NOT be affected

#### Scenario: Cancel logs audit event
- **WHEN** cancelation succeeds
- **THEN** the system SHALL log a `COMUNICACION_CANCELAR` audit event

#### Scenario: Cancel without authorization returns 403
- **WHEN** a user without `comunicacion:enviar` calls cancel
- **THEN** the system SHALL return 403 Forbidden

