## ADDED Requirements

### Requirement: AuthUser model
The system SHALL provide an AuthUser model as the authentication identity entity, separate from the full user profile. AuthUser fields SHALL be: id (UUID PK), tenant_id (UUID FK → Tenant), email (unique per tenant), password_hash (Argon2id), is_2fa_enabled (bool default False), otp_secret (encrypted, nullable), is_active (bool default True), created_at, updated_at, deleted_at. The model SHALL extend BaseModelMixin from C-02.

#### Scenario: Create AuthUser with valid data
- **WHEN** a new AuthUser is created with tenant_id, email, and password_hash
- **THEN** the system assigns a UUID id, sets created_at and updated_at to current timestamp, and deleted_at SHALL be NULL

#### Scenario: Email uniqueness per tenant
- **WHEN** creating a second AuthUser with the same (tenant_id, email) combination as an existing active user
- **THEN** the system SHALL raise an IntegrityError due to the UNIQUE(tenant_id, email) constraint

#### Scenario: Same email in different tenants is allowed
- **WHEN** creating an AuthUser with the same email but a different tenant_id
- **THEN** the creation SHALL succeed (uniqueness is scoped to tenant)

#### Scenario: Soft delete preserves email uniqueness
- **WHEN** an AuthUser is soft-deleted and a new AuthUser is created with the same (tenant_id, email)
- **THEN** the creation SHALL succeed if there is a partial unique index filtering on deleted_at IS NULL
- **NOTE**: The partial index must be implemented as part of migration 002 for this to work

#### Scenario: AuthUser requires tenant_id
- **WHEN** creating an AuthUser without a tenant_id
- **THEN** the system SHALL raise an IntegrityError (tenant_id is NOT NULL)

### Requirement: Argon2id password hashing
The system SHALL hash passwords using Argon2id before storing them in password_hash. The hash function SHALL use a random salt per operation. Verification SHALL compare a plaintext password against a stored hash using Argon2id.

#### Scenario: Hash and verify password
- **WHEN** a password is hashed with Argon2id and then verified with the same plaintext
- **THEN** verification SHALL return True

#### Scenario: Wrong password fails verification
- **WHEN** verifying a wrong password against a stored hash
- **THEN** verification SHALL return False

#### Scenario: Same password produces different hashes
- **WHEN** hashing the same password twice
- **THEN** the two hashes SHALL be different (due to random salt)

### Requirement: AuthUser active flag
The system SHALL check the is_active flag during login. Inactive users SHALL NOT be able to authenticate.

#### Scenario: Inactive user cannot login
- **WHEN** an AuthUser has is_active = False and attempts to log in with valid credentials
- **THEN** the system SHALL return a generic 401 error (same as wrong credentials, preventing user enumeration)

#### Scenario: Active user can login
- **WHEN** an AuthUser has is_active = True and provides valid credentials
- **THEN** the system SHALL proceed to the next step in the login flow
