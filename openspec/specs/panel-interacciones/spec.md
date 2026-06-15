## ADDED Requirements

### Requirement: Acciones por día (time-series)
The system SHALL return a time-series of daily action counts from the audit log, filterable by date range. This populates the "acciones por día" chart in the supervision panel (F9.1).

#### Scenario: Default last-30-days range
- **WHEN** the client calls GET /api/auditoria/panel/acciones-por-dia without date filters
- **THEN** the system SHALL return daily action counts for the last 30 days, ordered by date ascending

#### Scenario: Custom date range
- **WHEN** the client calls GET /api/auditoria/panel/acciones-por-dia?fecha_desde=2026-01-01&fecha_hasta=2026-01-31
- **THEN** the system SHALL return daily action counts only within that range

#### Scenario: COORDINADOR scope — own actions only
- **WHEN** a COORDINADOR with `auditoria:ver` calls the endpoint
- **THEN** the system SHALL count only actions where `actor_id` equals the COORDINADOR's user_id

#### Scenario: ADMIN scope — all actions
- **WHEN** an ADMIN with `auditoria:ver` calls the endpoint
- **THEN** the system SHALL count actions for all users in the tenant

#### Scenario: FINANZAS scope — all actions
- **WHEN** a FINANZAS user with `auditoria:ver` calls the endpoint
- **THEN** the system SHALL count actions for all users in the tenant

#### Scenario: Unauthorized access returns 403
- **WHEN** a user without `auditoria:ver` permission calls the endpoint
- **THEN** the system SHALL return 403 Forbidden

#### Scenario: Response format
- **WHEN** the endpoint returns successfully
- **THEN** the response SHALL include an `items` array of `{dia, total_acciones}` objects and the effective `desde`/`hasta` date range used

### Requirement: Estado de comunicaciones por docente
The system SHALL return the distribution of communication states (Pendiente, Enviando, Enviado, Error, Cancelado) aggregated by teacher and materia, filterable by date range and materia (F9.1). Queries the `comunicacion` table (E21).

#### Scenario: All teachers in date range
- **WHEN** the client calls GET /api/auditoria/panel/estado-comunicaciones with `fecha_desde` and `fecha_hasta`
- **THEN** the system SHALL return per-teacher counts of each communication state within that range

#### Scenario: Filter by materia
- **WHEN** the client passes `?materia_id=<uuid>`
- **THEN** the system SHALL return communication states only for that materia

#### Scenario: COORDINADOR scope — own communications only
- **WHEN** a COORDINADOR calls the endpoint
- **THEN** the system SHALL count only communications where `enviado_por` equals the COORDINADOR's user_id

#### Scenario: Comunicacion table not yet available (pre-C-12)
- **WHEN** the Comunicacion model/table does not exist or is empty
- **THEN** the system SHALL return an empty items array without error

#### Scenario: Response includes resolved names
- **WHEN** the endpoint returns successfully
- **THEN** each row SHALL include `usuario_nombre` and `materia_nombre` resolved from the corresponding tables

### Requirement: Interacciones por docente y materia
The system SHALL return usage metrics grouped by user, materia, and action type, filterable by date range (F9.1). Counts how many times each user performed each action on each materia.

#### Scenario: All interactions in date range
- **WHEN** the client calls GET /api/auditoria/panel/interacciones with `fecha_desde` and `fecha_hasta`
- **THEN** the system SHALL return rows grouped by `(actor_id, materia_id, accion)` with the count of each

#### Scenario: COORDINADOR scope — own interactions only
- **WHEN** a COORDINADOR calls the endpoint
- **THEN** the system SHALL return only rows where `actor_id` equals the COORDINADOR's user_id

#### Scenario: ADMIN sees all interactions
- **WHEN** an ADMIN calls the endpoint
- **THEN** the system SHALL return interactions for all users in the tenant

#### Scenario: Response format
- **WHEN** the endpoint returns successfully
- **THEN** each row SHALL include `usuario_id`, `usuario_nombre`, `materia_id`, `materia_nombre`, `accion`, and `cantidad`, sorted by `cantidad` descending

### Requirement: Últimas acciones (configurable limit)
The system SHALL return the most recent audit log entries, with a configurable maximum count (default 200, per F9.1). Supports optional filters for date range, user, and materia.

#### Scenario: Default limit of 200
- **WHEN** the client calls GET /api/auditoria/panel/ultimas-acciones without a limit parameter
- **THEN** the system SHALL return at most 200 entries, ordered by `fecha_hora` descending

#### Scenario: Custom limit
- **WHEN** the client passes `?limit=50`
- **THEN** the system SHALL return at most 50 entries

#### Scenario: Limit capped at 1000
- **WHEN** the client passes `?limit=5000`
- **THEN** the system SHALL cap the limit at 1000 entries

#### Scenario: Filter by date range
- **WHEN** the client passes `?fecha_desde=2026-05-01&fecha_hasta=2026-05-31`
- **THEN** the system SHALL return only entries within that date range

#### Scenario: Filter by usuario
- **WHEN** the client passes `?usuario_id=<uuid>`
- **THEN** the system SHALL return only entries where `actor_id` equals that user

#### Scenario: Filter by materia
- **WHEN** the client passes `?materia_id=<uuid>`
- **THEN** the system SHALL return only entries for that materia

#### Scenario: COORDINADOR scope — own entries only
- **WHEN** a COORDINADOR calls the endpoint
- **THEN** the system SHALL NOT need the `usuario_id` filter to scope — it automatically applies `actor_id = current_user`

#### Scenario: Response includes resolved names and max_registros
- **WHEN** the endpoint returns successfully
- **THEN** the response SHALL include `items` array of entries (with resolved `actor_nombre` and `materia_nombre`) and `max_registros` reflecting the actual limit applied
