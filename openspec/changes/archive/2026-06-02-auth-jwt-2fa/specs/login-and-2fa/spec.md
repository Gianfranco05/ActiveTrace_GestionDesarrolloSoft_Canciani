## ADDED Requirements

### Requirement: Login with email and password
The system SHALL provide a login endpoint at POST /api/auth/login accepting email and password. The system SHALL look up the AuthUser by email, verify the password with Argon2id, and check the is_active flag. If the user has 2FA disabled, the system SHALL issue access + refresh tokens. If 2FA is enabled, the system SHALL return a requires_2fa flag and a temporary session token.

#### Scenario: Successful login without 2FA
- **WHEN** a user provides valid email and password AND has is_2fa_enabled = False
- **THEN** the system returns 200 with access_token, refresh_token, and token_type = "bearer"

#### Scenario: Login with wrong password
- **WHEN** a user provides a valid email but wrong password
- **THEN** the system returns 401 with a generic error message (does not reveal which field is wrong)

#### Scenario: Login with non-existent email
- **WHEN** a user provides an email that does not exist
- **THEN** the system returns 401 with a generic error message (same as wrong password, preventing enumeration)

#### Scenario: Login with 2FA enabled
- **WHEN** a user provides valid credentials AND has is_2fa_enabled = True
- **THEN** the system returns 200 with requires_2fa = true and a session_token for completing 2FA (no access or refresh tokens issued yet)

#### Scenario: Login for inactive user
- **WHEN** a user with is_active = False provides valid credentials
- **THEN** the system returns 401 with a generic error message

### Requirement: TOTP enrollment
The system SHALL provide a 2FA enrollment endpoint at POST /api/auth/2fa/enroll (authenticated). It SHALL generate a TOTP secret using pyotp, return the base32 secret and a QR URI for the authenticator app. The secret SHALL be stored temporarily until verified.

#### Scenario: Enroll in 2FA
- **WHEN** an authenticated user calls POST /api/auth/2fa/enroll
- **THEN** the system returns secret_base32 (string) and qr_uri (string with otpauth:// format)

### Requirement: TOTP verification during enrollment
The system SHALL provide a verification endpoint at POST /api/auth/2fa/verify (authenticated). It SHALL accept a TOTP code, verify it against the temporary secret, and if valid, encrypt the secret with AES-256, store it in otp_secret, and set is_2fa_enabled = True.

#### Scenario: Verify TOTP code enables 2FA
- **WHEN** an authenticated user provides a valid TOTP code matching the temporary secret from enrollment
- **THEN** the system encrypts the secret with AES-256, stores it in AuthUser.otp_secret, sets is_2fa_enabled = True, and returns 200

#### Scenario: Invalid TOTP code fails enrollment
- **WHEN** an authenticated user provides an invalid TOTP code
- **THEN** the system returns 400 with an error message, and 2FA remains disabled

### Requirement: TOTP verification during login (2FA gate)
The system SHALL provide a second-factor verification endpoint at POST /api/auth/2fa/verify-login accepting a session_token (from step 5 of login) and a TOTP code. If the TOTP is valid, the system SHALL issue access + refresh tokens.

#### Scenario: Complete login with valid 2FA code
- **WHEN** a user with is_2fa_enabled = True provides valid credentials (gets session_token), then calls verify-login with the session_token and a valid TOTP code
- **THEN** the system returns 200 with access_token, refresh_token, and token_type = "bearer"

#### Scenario: Complete login with invalid 2FA code
- **WHEN** a user provides a valid session_token but an invalid TOTP code
- **THEN** the system returns 401 with an error message

#### Scenario: Complete login with expired session_token
- **WHEN** a user provides an expired session_token (after 5 minutes) with a valid TOTP code
- **THEN** the system returns 401 with an error message

### Requirement: Disable 2FA
The system SHALL provide a 2FA disable endpoint at POST /api/auth/2fa/disable (authenticated). It SHALL require password confirmation before disabling.

#### Scenario: Disable 2FA with correct password
- **WHEN** an authenticated user provides their current password and confirms disabling 2FA
- **THEN** the system clears otp_secret, sets is_2fa_enabled = False, and returns 200

#### Scenario: Disable 2FA with wrong password fails
- **WHEN** an authenticated user provides a wrong password
- **THEN** the system returns 401 and 2FA remains enabled
