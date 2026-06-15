## ADDED Requirements

### Requirement: Access token creation
The system SHALL create a signed JWT access token containing claims: sub (user_id as string), tenant_id (as string), roles (list of strings), exp (expiration timestamp), iat (issued at timestamp). The access token SHALL expire after ACCESS_TOKEN_EXPIRE_MINUTES (default 15 minutes). The token SHALL be signed with HS256 using SECRET_KEY.

#### Scenario: Create valid access token
- **WHEN** creating an access token for a known user_id, tenant_id, and roles
- **THEN** the system returns a JWT string that can be decoded and verified, containing sub, tenant_id, roles, exp, and iat

#### Scenario: Access token expires
- **WHEN** an access token is used after its expiration time
- **THEN** token verification SHALL raise an error (expired token)

#### Scenario: Tampered token is rejected
- **WHEN** a JWT's payload is modified after signing (tampered token)
- **THEN** signature verification SHALL fail

### Requirement: Refresh token creation and storage
The system SHALL provide opaque refresh tokens (64 bytes hex, via secrets.token_hex). Refresh tokens SHALL be stored as SHA-256 hash in the refresh_token table with user_id, tenant_id, expires_at, and is_used (default False). Refresh tokens SHALL expire after REFRESH_TOKEN_EXPIRE_DAYS (default 7 days).

#### Scenario: Create refresh token
- **WHEN** creating a refresh token for an AuthUser
- **THEN** the system returns an opaque string and stores its SHA-256 hash in the refresh_token table with the correct user_id, tenant_id, and expires_at (now + 7 days)

#### Scenario: Refresh token hash is irreversible
- **WHEN** the refresh_token table is inspected
- **THEN** the stored token_hash SHALL be the SHA-256 hash, not the raw token value

### Requirement: Token refresh with rotation
The system SHALL provide a refresh endpoint that accepts a valid refresh token, marks it as used (is_used = True), and issues a new access + refresh pair. The new refresh token SHALL be stored with a fresh expiry.

#### Scenario: Successful token refresh
- **WHEN** a valid, unused, non-expired refresh token is presented to the refresh endpoint
- **THEN** the system marks the old token as is_used = True, issues a new access token, and issues a new refresh token stored in the DB

#### Scenario: Used refresh token is rejected
- **WHEN** a refresh token with is_used = True is presented
- **THEN** the system SHALL return a 401 error

#### Scenario: Expired refresh token is rejected
- **WHEN** a refresh token past its expires_at is presented
- **THEN** the system SHALL return a 401 error

#### Scenario: Nonexistent refresh token is rejected
- **WHEN** a random string that does not match any stored hash is presented
- **THEN** the system SHALL return a 401 error

### Requirement: Compromise detection on refresh reuse
The system SHALL detect when an already-used refresh token is presented again. In that case, ALL refresh tokens for that user SHALL be invalidated (all set to is_used = True). The event SHALL be logged.

#### Scenario: Reuse of rotated token invalidates all sessions
- **WHEN** an attacker presents a refresh token that was already used in a previous rotation AND the legitimate user's new token is still valid
- **THEN** both the old and new refresh tokens SHALL be invalidated (is_used = True for all tokens belonging to that user)

### Requirement: Logout invalidates refresh token
The system SHALL provide a logout endpoint that marks the presented refresh token as used (is_used = True).

#### Scenario: Logout invalidates specific refresh token
- **WHEN** a user logs out presenting a valid refresh token
- **THEN** that specific refresh token SHALL be marked as is_used = True

#### Scenario: Logout with invalid token returns error
- **WHEN** a user logs out presenting a non-existent or already-used refresh token
- **THEN** the system SHALL return a 401 error
