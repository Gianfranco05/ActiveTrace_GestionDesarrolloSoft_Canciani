## ADDED Requirements

### Requirement: get_current_user dependency
The system SHALL provide a FastAPI dependency `get_current_user` that extracts the JWT from the Authorization header (Bearer scheme), verifies the token (signature + expiry), decodes the payload, and returns a UserSession dataclass with user_id (UUID), tenant_id (UUID), and roles (list[str]). The dependency SHALL also inject the resolved UserSession into request.state.user.

#### Scenario: Valid JWT returns UserSession
- **WHEN** a request includes a valid, non-expired JWT in the Authorization header
- **THEN** get_current_user returns a UserSession with the correct user_id, tenant_id, and roles from the token, and request.state.user is set

#### Scenario: Missing Authorization header
- **WHEN** a request has no Authorization header
- **THEN** get_current_user raises HTTPException(401)

#### Scenario: Non-Bearer Authorization header
- **WHEN** a request has an Authorization header that does not start with "Bearer "
- **THEN** get_current_user raises HTTPException(401)

#### Scenario: Expired JWT
- **WHEN** a request includes an expired JWT
- **THEN** get_current_user raises HTTPException(401)

#### Scenario: Tampered JWT (invalid signature)
- **WHEN** a request includes a JWT with a tampered payload
- **THEN** signature verification fails and get_current_user raises HTTPException(401)

### Requirement: get_tenant dependency
The system SHALL provide a FastAPI dependency `get_tenant` that extracts tenant_id from the authenticated UserSession and returns it as a UUID. This dependency SHALL require get_current_user as a sub-dependency.

#### Scenario: get_tenant returns tenant_id from authenticated user
- **WHEN** a valid authenticated request is made
- **THEN** get_tenant returns the tenant_id UUID from the UserSession

#### Scenario: get_tenant fails without auth
- **WHEN** a non-authenticated request is made to an endpoint requiring get_tenant
- **THEN** the dependency chain raises HTTPException(401) because get_current_user fails first

### Requirement: UserSession dataclass
The system SHALL define a UserSession dataclass with fields: user_id (UUID), tenant_id (UUID), roles (list[str]). This SHALL be the standard representation of an authenticated user across the application.

#### Scenario: UserSession construction
- **WHEN** creating a UserSession with user_id, tenant_id, and roles
- **THEN** the fields are accessible and typed correctly as UUID, UUID, and list[str]

### Requirement: Identity never from request parameters
The system SHALL enforce that user identity and tenant_id are NEVER derived from request parameters (query string, body, headers other than Authorization). The `get_current_user` dependency is the sole source of identity.

#### Scenario: Identity from JWT overrides body parameters
- **WHEN** a request includes a user_id in the request body AND a valid JWT with a different user_id
- **THEN** the system uses the JWT's user_id, not the body parameter (enforced by design — body parameters are never used for identity)
