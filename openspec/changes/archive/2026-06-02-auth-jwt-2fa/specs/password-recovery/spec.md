## ADDED Requirements

### Requirement: Forgot password — generate reset token
The system SHALL provide a forgot password endpoint at POST /api/auth/forgot accepting an email. If the email exists, the system SHALL generate a one-time reset token (URL-safe random string), store its SHA-256 hash in the reset_token table with a 30-minute expiry, and log the reset URL (placeholder for real email in C-12). The endpoint SHALL always return 200 regardless of whether the email exists.

#### Scenario: Forgot password for existing email
- **WHEN** a valid email that exists in AuthUser is submitted to POST /api/auth/forgot
- **THEN** the system creates a reset_token record with the correct user_id, token_hash, expires_at (now + 30min), is_used = False, and returns 200

#### Scenario: Forgot password for non-existent email (no enumeration)
- **WHEN** an email that does not exist is submitted to POST /api/auth/forgot
- **THEN** the system returns 200 (same response as existing email, preventing email enumeration) and does NOT create a reset_token record

### Requirement: Reset password with valid token
The system SHALL provide a reset password endpoint at POST /api/auth/reset accepting a token and new_password. It SHALL hash the token, look it up in the reset_token table, verify it is not expired and not used. If valid, it SHALL hash the new password with Argon2id, update AuthUser.password_hash, invalidate ALL refresh tokens for that user, and mark the reset_token as used.

#### Scenario: Reset password with valid token
- **WHEN** a valid, unexpired, unused reset token is presented with a new password meeting strength requirements
- **THEN** the system hashes the new password with Argon2id, updates AuthUser.password_hash, invalidates all refresh tokens for that user (is_used = True), marks the reset_token as used, and returns 200

#### Scenario: Reset password with expired token
- **WHEN** a reset token past its 30-minute expiry is presented
- **THEN** the system returns 400 with "Invalid or expired token"

#### Scenario: Reset password with already-used token
- **WHEN** a reset token that was previously used is presented again
- **THEN** the system returns 400 with "Invalid or expired token"

#### Scenario: Reset password with weak password
- **WHEN** a new password does not meet strength requirements (min 8 chars, 1 uppercase, 1 number)
- **THEN** the system returns 422 with a validation error

### Requirement: Password change invalidates all sessions
The system SHALL invalidate ALL refresh tokens for a user whenever their password is changed (either through password reset or password change).

#### Scenario: After password reset, old tokens are invalid
- **WHEN** a user changes their password via reset endpoint
- **THEN** all existing refresh tokens for that user SHALL have is_used = True, forcing re-login
