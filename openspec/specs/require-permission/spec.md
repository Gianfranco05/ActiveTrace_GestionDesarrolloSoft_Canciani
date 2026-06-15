# require-permission Specification

## Purpose
TBD - created by archiving change rbac-permisos-finos. Update Purpose after archive.
## Requirements
### Requirement: require_permission FastAPI dependency
The system SHALL provide a FastAPI dependency `require_permission(codigo: str)` that checks whether the current authenticated user has the specified permission. The dependency SHALL:
1. Resolve the current user via `get_current_user` (from C-03) to obtain `UserSession` with roles
2. Query effective permissions for the user's roles via RbacRepository
3. If the required codigo is in the effective set → allow the request to proceed
4. If NOT → raise HTTPException(403) with detail "Forbidden"

The dependency MAY be used as: `Depends(require_permission("modulo:accion"))`.

#### Scenario: User with permission passes the guard
- **WHEN** an authenticated user whose roles include the required permission accesses a protected endpoint
- **THEN** the dependency SHALL NOT raise an exception and the request proceeds to the endpoint handler

#### Scenario: User without permission receives 403
- **WHEN** an authenticated user whose roles do NOT include the required permission accesses a protected endpoint
- **THEN** the dependency SHALL raise HTTPException(403)

#### Scenario: Unauthenticated user receives 401 (not 403)
- **WHEN** a request without a valid JWT accesses an endpoint protected by require_permission
- **THEN** the dependency chain SHALL first fail at get_current_user with HTTPException(401) — authentication failure takes precedence over authorization

#### Scenario: User with empty roles receives 403
- **WHEN** an authenticated user with an empty roles list accesses any protected endpoint
- **THEN** the dependency SHALL raise HTTPException(403) (fail-closed: no roles → no permissions)

#### Scenario: Guard is idempotent
- **WHEN** require_permission("modulo:accion") is called twice in the same request for the same user
- **THEN** both calls SHALL produce the same result (allowing or denying consistently)

### Requirement: require_permission returns UserSession (convenience variant)
The system SHALL provide a convenience variant `require_permission_return_user(codigo: str)` that behaves identically to `require_permission` but returns the `UserSession` for the endpoint handler to use, avoiding a separate `Depends(get_current_user)` declaration.

#### Scenario: Guard returns UserSession when permission is granted
- **WHEN** a valid user with permission uses the convenience variant
- **THEN** the dependency returns the UserSession with user_id, tenant_id, and roles

### Requirement: 403 response format
The system SHALL return a consistent 403 response body when authorization fails: `{"detail": "Forbidden"}`. The response SHALL have HTTP status 403 Forbidden.

#### Scenario: 403 response matches format
- **WHEN** require_permission denies access
- **THEN** the response SHALL have status 403 and body `{"detail": "Forbidden"}`

