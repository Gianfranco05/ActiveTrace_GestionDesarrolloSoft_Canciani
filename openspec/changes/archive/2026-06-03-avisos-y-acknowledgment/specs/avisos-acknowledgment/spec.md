# avisos-acknowledgment Specification

## Purpose
Confirmación de lectura de avisos (RN-19) y contadores derivados de la tabla AcknowledgmentAviso. Los contadores NO se almacenan como campos denormalizados en Aviso; se calculan en tiempo real consultando AcknowledgmentAviso.

## ADDED Requirements

### Requirement: Confirmar lectura de aviso (acknowledgment) (RN-19, FL-09 paso 4)
The system SHALL allow any authenticated user to confirm (acknowledge) having read an aviso that requires acknowledgment. The confirmation SHALL be idempotent per user per aviso.

- Method: POST
- Path: `/api/avisos/{aviso_id}/ack`
- Guard: `require_permission("aviso:confirmar")` (all roles have this permission)
- Request body: none
- Response 201: `AckResponse` with `aviso_id`, `usuario_id`, `confirmado_at`
- The system SHALL return 404 if the aviso does not exist, is soft-deleted, or is not visible to the user (outside vigencia OR wrong scope)
- The system SHALL return 422 if the aviso does not have `requiere_ack=true`
- The system SHALL be idempotent: if the user already has an `AcknowledgmentAviso` record for this aviso, return 200 with the existing `confirmado_at`
- The system SHALL NOT create duplicate `AcknowledgmentAviso` records for the same (aviso_id, usuario_id) pair
- The system SHALL audit the operation with `AVISO_CONFIRMAR`

#### Scenario: Confirmar aviso exitosamente
- **WHEN** an ALUMNO sends POST /api/avisos/{id}/ack for a visible aviso with `requiere_ack=true` and no prior acknowledgment
- **THEN** the system SHALL create an `AcknowledgmentAviso` record with the current timestamp
- **AND** respond 201 with `aviso_id`, `usuario_id`, `confirmado_at`
- **AND** the aviso SHALL no longer appear in GET /api/avisos for that user
- **AND** the system SHALL generate an audit log entry with code `AVISO_CONFIRMAR`

#### Scenario: Confirmar aviso ya confirmado (idempotencia)
- **WHEN** an ALUMNO sends POST /api/avisos/{id}/ack for an aviso they already acknowledged
- **THEN** the system SHALL return 200 with the existing `confirmado_at` (not 201)
- **AND** the system SHALL NOT create a duplicate `AcknowledgmentAviso` record

#### Scenario: Confirmar aviso que no requiere ack
- **WHEN** an ALUMNO sends POST /api/avisos/{id}/ack for an aviso with `requiere_ack=false`
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Confirmar aviso fuera de vigencia
- **WHEN** an ALUMNO sends POST /api/avisos/{id}/ack for an aviso outside its visibility window (`inicio_en` > now OR `fin_en` < now)
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Confirmar aviso no visible por scope
- **WHEN** a PROFESOR sends POST /api/avisos/{id}/ack for an aviso with `alcance=PorCohorte` and a `cohorte_id` the PROFESOR is NOT assigned to
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Confirmar aviso sin autenticación
- **WHEN** an unauthenticated request sends POST /api/avisos/{id}/ack
- **THEN** the system SHALL respond 401 Unauthorized

### Requirement: Obtener contadores de vistas y confirmaciones de un aviso
The system SHALL provide an endpoint to retrieve acknowledgment statistics for a given aviso. Counters SHALL be derived from `AcknowledgmentAviso` table, NOT from denormalized fields on `Aviso`.

- Method: GET
- Path: `/api/avisos/{aviso_id}/ack/stats`
- Guard: `require_permission("avisos:publicar")` (COORDINADOR, ADMIN only)
- Response 200: `AckStatsResponse` with `aviso_id` (UUID), `total_views` (int — count of distinct users who accessed the aviso detail), `total_acks` (int — count of AcknowledgmentAviso records), `pendientes_ack` (int — total_views - total_acks, only meaningful when `requiere_ack=true`)
- The system SHALL return 404 if the aviso does not exist or is soft-deleted
- The `total_views` count SHALL be computed as `COUNT(DISTINCT usuario_id)` from `AcknowledgmentAviso` for this `aviso_id` (since viewing the detail and acknowledging are the only interactions tracked)

#### Scenario: Obtener stats de aviso con confirmaciones
- **WHEN** a COORDINADOR sends GET /api/avisos/{id}/ack/stats for an aviso with `requiere_ack=true` that has 5 acknowledgments from 5 different users
- **THEN** the system SHALL respond 200 with `total_views: 5`, `total_acks: 5`, `pendientes_ack: 0`

#### Scenario: Obtener stats de aviso sin confirmaciones
- **WHEN** a COORDINADOR sends GET /api/avisos/{id}/ack/stats for an aviso with `requiere_ack=true` that has 0 acknowledgments
- **THEN** the system SHALL respond 200 with `total_views: 0`, `total_acks: 0`, `pendientes_ack: 0`

#### Scenario: Obtener stats de aviso inexistente
- **WHEN** a COORDINADOR sends GET /api/avisos/{non-existent-id}/ack/stats
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Obtener stats sin permisos
- **WHEN** a user without `avisos:publicar` sends GET /api/avisos/{id}/ack/stats
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Determinación del estado de acknowledgment por usuario
The system SHALL, when returning aviso detail or list items, include a boolean `acknowledged` field indicating whether the current authenticated user has confirmed that aviso.

- The `acknowledged` field SHALL be `true` if an `AcknowledgmentAviso` record exists for (aviso_id, current_user_id)
- The `acknowledged` field SHALL be `false` otherwise
- This applies to both `GET /api/avisos` (list items) and `GET /api/avisos/{aviso_id}` (detail)

#### Scenario: Aviso no confirmado muestra acknowledged=false
- **WHEN** a user who has NOT acknowledged an aviso with `requiere_ack=true` calls GET /api/avisos/{id}
- **THEN** the response SHALL include `acknowledged: false`

#### Scenario: Aviso confirmado muestra acknowledged=true
- **WHEN** a user who HAS acknowledged an aviso with `requiere_ack=true` calls GET /api/avisos/{id}
- **THEN** the response SHALL include `acknowledged: true`
