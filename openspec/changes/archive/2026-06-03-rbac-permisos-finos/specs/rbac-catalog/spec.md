## ADDED Requirements

### Requirement: List roles endpoint
The system SHALL provide a GET endpoint at `/api/v1/rbac/roles` that returns all non-deleted roles for the current tenant. The endpoint SHALL require `usuarios:gestionar` permission.

#### Scenario: List roles returns tenant-scoped roles
- **WHEN** an authenticated ADMIN calls GET /api/v1/rbac/roles
- **THEN** the response SHALL return a list of roles with id, nombre, descripcion for the current tenant only

#### Scenario: List roles without permission returns 403
- **WHEN** an authenticated user without usuarios:gestionar calls GET /api/v1/rbac/roles
- **THEN** the response SHALL be 403 Forbidden

### Requirement: Create role endpoint
The system SHALL provide a POST endpoint at `/api/v1/rbac/roles` that creates a new role. The endpoint SHALL require `usuarios:gestionar` permission. Request body: `{ nombre: str, descripcion: str | None }`.

#### Scenario: Create role succeeds
- **WHEN** an ADMIN calls POST /api/v1/rbac/roles with a unique nombre valid for the tenant
- **THEN** the response SHALL return 201 with the created role id, nombre, descripcion

#### Scenario: Create duplicate role nombre returns 409
- **WHEN** an ADMIN calls POST /api/v1/rbac/roles with a nombre that already exists for the tenant
- **THEN** the response SHALL return 409 Conflict

### Requirement: Get role with permissions endpoint
The system SHALL provide a GET endpoint at `/api/v1/rbac/roles/{id}` that returns a role with its assigned permissions. The endpoint SHALL require `usuarios:gestionar` permission.

#### Scenario: Get role returns role with permiso codigos
- **WHEN** an ADMIN calls GET /api/v1/rbac/roles/{id}
- **THEN** the response SHALL include the role's id, nombre, descripcion, and a list of permiso codigos

### Requirement: Update role endpoint
The system SHALL provide a PUT endpoint at `/api/v1/rbac/roles/{id}` that updates a role's nombre and/or descripcion. The endpoint SHALL require `usuarios:gestionar` permission.

#### Scenario: Update role succeeds
- **WHEN** an ADMIN calls PUT /api/v1/rbac/roles/{id} with updated nombre or descripcion
- **THEN** the response SHALL return the updated role

### Requirement: Set role permissions endpoint
The system SHALL provide a PUT endpoint at `/api/v1/rbac/roles/{id}/permisos` that replaces all permissions for a role. The endpoint SHALL require `usuarios:gestionar` permission. Request body: `{ permiso_ids: list[UUID] }`.

#### Scenario: Set permissions replaces all
- **WHEN** an ADMIN calls PUT /api/v1/rbac/roles/{id}/permisos with a list of permiso_ids
- **THEN** all previous RolPermiso entries for that rol SHALL be removed and replaced with the new mappings

### Requirement: List all permissions endpoint
The system SHALL provide a GET endpoint at `/api/v1/rbac/permisos` that returns the global permission catalog. The endpoint SHALL require `usuarios:gestionar` permission.

#### Scenario: List permissions returns all codigos
- **WHEN** an ADMIN calls GET /api/v1/rbac/permisos
- **THEN** the response SHALL return a list of all permissions with id, codigo, descripcion

### Requirement: Create permission endpoint
The system SHALL provide a POST endpoint at `/api/v1/rbac/permisos` that creates a new permission in the global catalog. The endpoint SHALL require `usuarios:gestionar` permission. Request body: `{ codigo: str, descripcion: str | None }`.

#### Scenario: Create permission succeeds
- **WHEN** an ADMIN calls POST /api/v1/rbac/permisos with a unique codigo
- **THEN** the response SHALL return 201 with the created permission id, codigo, descripcion

#### Scenario: Create duplicate permission codigo returns 409
- **WHEN** an ADMIN calls POST /api/v1/rbac/permisos with a codigo that already exists
- **THEN** the response SHALL return 409 Conflict
