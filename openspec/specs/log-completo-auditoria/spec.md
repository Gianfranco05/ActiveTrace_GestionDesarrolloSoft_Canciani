## ADDED Requirements

### Requirement: Log completo de auditoría con filtros mejorados
The system SHALL provide a paginated, filterable list of all audit log entries, extending the foundation from C-05 with additional filters: `materia_id`, `usuario_id` (actor), `ip` (partial match), and `accion` (action code). Sorted by `fecha_hora` descending per RN-23 (F9.2).

#### Scenario: List with no filters — default pagination
- **WHEN** the client calls GET /api/auditoria/log without any query parameters
- **THEN** the system SHALL return the first page (offset=0, limit=50) of all audit entries in the tenant, ordered by `fecha_hora DESC`

#### Scenario: Filter by date range
- **WHEN** the client passes `?fecha_desde=2026-01-01T00:00:00Z&fecha_hasta=2026-06-30T23:59:59Z`
- **THEN** the system SHALL return only entries whose `fecha_hora` falls within that range

#### Scenario: Filter by materia_id
- **WHEN** the client passes `?materia_id=<uuid>`
- **THEN** the system SHALL return only entries where `materia_id` equals that value

#### Scenario: Filter by usuario_id (actor)
- **WHEN** the client passes `?usuario_id=<uuid>`
- **THEN** the system SHALL return only entries where `actor_id` equals that user

#### Scenario: Filter by accion (action code)
- **WHEN** the client passes `?accion=CALIFICACIONES_IMPORTAR`
- **THEN** the system SHALL return only entries with that action code

#### Scenario: Filter by IP (partial match)
- **WHEN** the client passes `?ip=192.168`
- **THEN** the system SHALL return only entries whose `ip` field contains that substring

#### Scenario: Multiple combined filters
- **WHEN** the client passes `?fecha_desde=2026-05-01&usuario_id=<uuid>&accion=COMUNICACION_ENVIAR`
- **THEN** the system SHALL apply ALL filters with AND logic

#### Scenario: Pagination
- **WHEN** the client passes `?offset=50&limit=25`
- **THEN** the system SHALL return entries starting from position 50, limited to 25 entries, with `total` indicating the total matching count

#### Scenario: COORDINADOR scope — own entries only
- **WHEN** a COORDINADOR with `auditoria:ver` calls the endpoint
- **THEN** the system SHALL automatically filter by `actor_id = current_user.user_id`, regardless of any `usuario_id` parameter provided
- **AND** if `usuario_id` is provided and differs from the COORDINADOR's own ID, the system SHALL return an empty result set

#### Scenario: ADMIN sees all entries
- **WHEN** an ADMIN calls the endpoint
- **THEN** the system SHALL return entries for all users in the tenant
- **AND** the `usuario_id` filter SHALL be honored if provided

#### Scenario: FINANZAS sees all entries
- **WHEN** a FINANZAS user calls the endpoint
- **THEN** the system SHALL return entries for all users in the tenant

#### Scenario: Unauthorized access returns 403
- **WHEN** a user without `auditoria:ver` permission calls the endpoint
- **THEN** the system SHALL return 403 Forbidden

#### Scenario: Audit log is read-only — no POST/PUT/DELETE
- **WHEN** any client attempts POST, PUT, PATCH, or DELETE on the audit log endpoint
- **THEN** the system SHALL return 405 Method Not Allowed

### Requirement: Resolved actor names in log response
The system SHALL resolve `actor_id` to a human-readable name in the log response by joining with the `auth_user` table. This avoids the frontend having to resolve user names separately (F9.2).

#### Scenario: Log entry includes resolved actor name
- **WHEN** the system returns a log entry
- **THEN** the response SHALL include `actor_nombre` (concatenation of auth_user fields) alongside `actor_id`

#### Scenario: Deleted user reference — actor name is null
- **WHEN** an audit log entry references a user that no longer exists (soft-deleted)
- **THEN** the system SHALL return `actor_nombre: null` and not omit the entry

### Requirement: Respect immutable audit log constraint (RN-23)
The system SHALL NOT provide any mechanism to modify or delete audit log entries through the API. All endpoints under `/api/auditoria/` are read-only GET endpoints.

#### Scenario: No mutation endpoints exist
- **WHEN** an API consumer inspects the OpenAPI schema for `/api/auditoria/`
- **THEN** no POST, PUT, PATCH, or DELETE operations SHALL be registered under that prefix
