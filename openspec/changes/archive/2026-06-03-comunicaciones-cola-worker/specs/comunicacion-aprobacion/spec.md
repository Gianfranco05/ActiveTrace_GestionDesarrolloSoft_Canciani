## ADDED Requirements

### Requirement: Approval configurable by tenant (RN-17)
The system SHALL support configurable approval for mass communications at the tenant level. When a tenant has `requiere_aprobacion_comunicaciones = True`, all mass enqueues SHALL require explicit approval before the worker processes them.

#### Scenario: Tenant without approval processes directly
- **WHEN** a tenant has `requiere_aprobacion_comunicaciones = False`
- **THEN** messages enqueued by that tenant SHALL be processed by the worker immediately
- **AND** `requiere_aprobacion` SHALL be stored as `false` on each Comunicacion record

#### Scenario: Tenant with approval blocks worker processing
- **WHEN** a tenant has `requiere_aprobacion_comunicaciones = True`
- **THEN** new Comunicacion records SHALL have `requiere_aprobacion = True`
- **AND** the worker SHALL skip these records until `aprobado_por` is set

#### Scenario: Approval flag is denormalized per record
- **WHEN** a Comunicacion record is created
- **THEN** the `requiere_aprobacion` field SHALL be set based on the tenant's current configuration
- **AND** changes to the tenant's configuration SHALL NOT affect existing records

### Requirement: Approve lote or individual (F3.3)
The system SHALL support approving Comunicacion records by lote (all pending messages in a batch) or by individual id. Only users with the `comunicacion:aprobar` permission SHALL be able to approve.

#### Scenario: Approve by lote_id
- **WHEN** an authorized user calls POST /api/comunicaciones/{lote_id}/aprobar
- **THEN** ALL records in that lote with `estado = 'Pendiente'` SHALL be approved
- **AND** `aprobado_por` SHALL be set to the current user's id
- **AND** the records SHALL remain in 'Pendiente' state (worker picks them up)

#### Scenario: Approve by individual id
- **WHEN** an authorized user calls POST /api/comunicaciones/{id}/aprobar with a single Comunicacion id
- **THEN** that specific record SHALL have `aprobado_por` set to the current user's id

#### Scenario: Approve ignores already-approved records
- **WHEN** calling approve on a lote where some records are already approved
- **THEN** the already-approved records SHALL NOT be modified
- **AND** the response SHALL indicate how many were newly approved

#### Scenario: Reject (cancel) by lote_id
- **WHEN** an authorized user calls POST /api/comunicaciones/{lote_id}/cancelar with intention to reject
- **THEN** ALL records in that lote with `estado = 'Pendiente'` SHALL transition to 'Cancelado'

#### Scenario: Approve without authorization returns 403
- **WHEN** a user without `comunicacion:aprobar` calls POST /api/comunicaciones/{id}/aprobar
- **THEN** the system SHALL return 403 Forbidden

#### Scenario: Approve non-existent lote returns 404
- **WHEN** the client calls POST /api/comunicaciones/{lote_id}/aprobar with a non-existent lote_id
- **THEN** the system SHALL return 404 Not Found

### Requirement: Approval audit trail
The system SHALL record all approval and rejection actions in the audit log.

#### Scenario: Approve logs COMUNICACION_APROBAR
- **WHEN** a lote is approved
- **THEN** the system SHALL log a `COMUNICACION_APROBAR` audit event
- **AND** the audit detail SHALL include the lote_id and number of approved records

#### Scenario: Reject logs COMUNICACION_CANCELAR
- **WHEN** a lote is rejected/cancelled by an approver
- **THEN** the system SHALL log a `COMUNICACION_CANCELAR` audit event
- **AND** the audit detail SHALL include the lote_id and number of cancelled records

### Requirement: Approval scope isolation
The system SHALL scope approval actions to the approver's tenant. A user from tenant A cannot approve communications from tenant B.

#### Scenario: Cross-tenant approval returns 404
- **WHEN** a user from tenant A calls approve on a lote_id from tenant B
- **THEN** the system SHALL return 404 Not Found (no information leak)
