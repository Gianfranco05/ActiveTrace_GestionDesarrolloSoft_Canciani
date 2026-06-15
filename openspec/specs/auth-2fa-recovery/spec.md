# auth-2fa-recovery Specification

## Purpose
TBD - created by archiving change frontend-shell-y-auth. Update Purpose after archive.
## Requirements
### Requirement: 2FA verification screen
The system SHALL provide a 2FA verification screen at `/2fa` with a 6-digit TOTP code input and a "Verificar" submit button. The screen SHALL only be accessible after a login response that includes `requires_2fa: true`.

#### Scenario: 2FA screen renders
- **WHEN** the user is redirected to `/2fa` after login with `requires_2fa: true`
- **THEN** a 6-digit code input and "Verificar" button SHALL be visible
- **AND** a descriptive text "Ingresá el código de verificación de tu aplicación de autenticación" SHALL be displayed

#### Scenario: 2FA form validates 6-digit code
- **WHEN** the user submits a code with fewer than 6 digits
- **THEN** an error message "El código debe tener 6 dígitos" SHALL be displayed

#### Scenario: 2FA verification succeeds
- **WHEN** the user enters a valid 6-digit TOTP code
- **THEN** `POST /api/auth/2fa/verify` SHALL be called with the temp_token and code
- **AND** the access and refresh tokens SHALL be stored in localStorage
- **AND** the user SHALL be redirected to `/`

#### Scenario: 2FA verification fails
- **WHEN** the user enters an invalid code
- **THEN** `POST /api/auth/2fa/verify` SHALL return 401
- **AND** an error message "Código inválido" SHALL be displayed
- **AND** the user SHALL remain on `/2fa`

### Requirement: Forgot password screen
The system SHALL provide a forgot password screen at `/forgot` with an email input and "Enviar enlace" submit button. On success, it SHALL display a confirmation message.

#### Scenario: Forgot password screen renders
- **WHEN** navigating to `/forgot`
- **THEN** an email input, "Enviar enlace" submit button, and a link to "Volver al inicio de sesión" SHALL be visible

#### Scenario: Forgot password form validates email
- **WHEN** the user submits an invalid email
- **THEN** an error message "Email inválido" SHALL be displayed

#### Scenario: Forgot password succeeds
- **WHEN** the user submits a valid email
- **THEN** `POST /api/auth/forgot` SHALL be called
- **AND** a success message "Si el email está registrado, recibirás un enlace para restablecer tu contraseña" SHALL be displayed
- **AND** the form SHALL be replaced by the confirmation message

#### Scenario: Forgot password always shows confirmation (security)
- **WHEN** the user submits an email that is NOT registered
- **THEN** the system SHALL show the SAME confirmation message as a successful submission
- **AND** `POST /api/auth/forgot` SHALL NOT indicate whether the email exists

### Requirement: Reset password screen
The system SHALL provide a reset password screen at `/reset?token=<token>` with new password and confirm password inputs, and a "Restablecer contraseña" submit button.

#### Scenario: Reset password screen renders
- **WHEN** navigating to `/reset?token=valid-token`
- **THEN** a new password input, confirm password input, and "Restablecer contraseña" button SHALL be visible

#### Scenario: Reset password validates token presence
- **WHEN** navigating to `/reset` without a token parameter
- **THEN** an error message "Enlace inválido o expirado" SHALL be displayed
- **AND** a link to `/forgot` SHALL be shown

#### Scenario: Reset password validates password strength
- **WHEN** the user submits a password shorter than 8 characters
- **THEN** an error message "La contraseña debe tener al menos 8 caracteres" SHALL be displayed

#### Scenario: Reset password validates passwords match
- **WHEN** the user submits different passwords in the two fields
- **THEN** an error message "Las contraseñas no coinciden" SHALL be displayed

#### Scenario: Reset password succeeds
- **WHEN** the user submits a valid token and matching passwords (≥8 chars)
- **THEN** `POST /api/auth/reset` SHALL be called with the token and new password
- **AND** a success message "Contraseña restablecida exitosamente" SHALL be displayed
- **AND** a link to `/login` SHALL be shown

#### Scenario: Reset password fails with invalid token
- **WHEN** the token is expired or invalid
- **THEN** `POST /api/auth/reset` SHALL return 400
- **AND** an error message "Enlace inválido o expirado" SHALL be displayed

