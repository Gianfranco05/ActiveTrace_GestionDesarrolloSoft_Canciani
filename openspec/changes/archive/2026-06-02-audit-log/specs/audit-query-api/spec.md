## ADDED Requirements

### Requirement: Audit response schemas
The system SHALL define Pydantic response schemas in `schemas/audit.py`:

- `AuditLogResponse` — id, fecha_hora (datetime), accion (str), actor_id (UUID), impersonado_id (UUID | None), materia_id (UUID | None), detalle (dict | None), filas_afectadas (int), ip (str | None), user_agent (str | None)
- `AuditLogListResponse` — items (list[AuditLogResponse]), total (int), offset (int), limit (int)

All schemas SHALL use `model_config = ConfigDict(extra='forbid')`.

#### Scenario: AuditLogResponse matches model fields
- **WHEN** serializing an AuditLog to AuditLogResponse
- **THEN** all fields SHALL match the model attributes

### Requirement: Audit log query endpoints
The system SHALL provide the following endpoints under `/api/v1/audit`:

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/api/v1/audit` | `auditoria:ver` | List audit logs with optional filters |
| GET | `/api/v1/audit/{id}` | `auditoria:ver` | Get single audit log entry |

#### GET /api/v1/audit query parameters
- `accion` (optional) — filter by action code
- `actor_id` (optional) — filter by actor UUID
- `fecha_desde` (optional) — filter start date (ISO datetime)
- `fecha_hasta` (optional) — filter end date (ISO datetime)
- `offset` (optional, default 0) — pagination offset
- `limit` (optional, default 50, max 100) — pagination limit

#### Scenario: List audit logs returns paginated results
- **WHEN** a user with `auditoria:ver` permission calls GET /api/v1/audit
- **THEN** a paginated list of AuditLogResponse items SHALL be returned

#### Scenario: List filters by accion
- **WHEN** calling GET /api/v1/audit?accion=CALIFICACIONES_IMPORTAR
- **THEN** only entries with that action SHALL be returned

#### Scenario: List filters by date range
- **WHEN** calling GET /api/v1/audit?fecha_desde=...&fecha_hasta=...
- **THEN** only entries within that range SHALL be returned

#### Scenario: List returns 403 without auditoria:ver
- **WHEN** a user WITHOUT `auditoria:ver` calls GET /api/v1/audit
- **THEN** a 403 Forbidden SHALL be returned

#### Scenario: List returns 401 without authentication
- **WHEN** an unauthenticated request calls GET /api/v1/audit
- **THEN** a 401 Unauthorized SHALL be returned

#### Scenario: List respects tenant isolation
- **WHEN** calling GET /api/v1/audit
- **THEN** only entries for the current user's tenant SHALL be returned

#### Scenario: Get single entry returns matching log
- **WHEN** calling GET /api/v1/audit/{id} with a valid id
- **THEN** the matching AuditLogResponse SHALL be returned

#### Scenario: Get single entry returns 404
- **WHEN** calling GET /api/v1/audit/{id} with a non-existent id
- **THEN** a 404 Not Found SHALL be returned
