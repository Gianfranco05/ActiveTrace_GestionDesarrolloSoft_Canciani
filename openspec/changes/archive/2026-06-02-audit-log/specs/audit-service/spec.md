## ADDED Requirements

### Requirement: AuditService
The system SHALL provide an `AuditService` class with a `log()` method that creates audit log entries with the current context:

```python
async def log(
    self,
    accion: AuditAction,
    actor_id: UUID,
    tenant_id: UUID,
    detalle: dict | None = None,
    filas_afectadas: int = 0,
    impersonado_id: UUID | None = None,
    materia_id: UUID | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuditLog: ...
```

The service SHALL use AuditLogRepository.create() internally.

#### Scenario: Log creates entry with all fields
- **WHEN** calling `log()` with all parameters provided
- **THEN** an AuditLog entry SHALL be created with all fields matching the input

#### Scenario: Log creates entry with defaults
- **WHEN** calling `log()` with only required fields (accion, actor_id, tenant_id)
- **THEN** an AuditLog entry SHALL be created with filas_afectadas=0, detalle=None, impersonado_id=None, materia_id=None, ip=None, user_agent=None

#### Scenario: Log returns the created entry
- **WHEN** calling `log()`
- **THEN** the return value SHALL be the created AuditLog with an assigned id

#### Scenario: Log with impersonation records both actors
- **WHEN** calling `log()` with an impersonado_id
- **THEN** the entry SHALL have both actor_id (the impersonator) and impersonado_id set
