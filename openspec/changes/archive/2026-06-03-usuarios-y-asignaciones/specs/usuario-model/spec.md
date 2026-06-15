## ADDED Requirements

### Requirement: Usuario ORM model (1:1 with AuthUser, PII encrypted)

The system SHALL define a Usuario ORM model representing the profile extension of AuthUser (C-03). The model SHALL extend BaseModelMixin (UUID PK, tenant_id FK, created_at, updated_at, deleted_at). The PK `id` SHALL be a FK to `auth_user.id` enforcing the 1:1 relationship.

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK + FK → auth_user.id (1:1), via BaseModelMixin |
| `tenant_id` | UUID | FK → Tenant(id), via BaseModelMixin |
| `nombre` | String(100) | NOT NULL |
| `apellidos` | String(100) | NOT NULL |
| `dni` | Text | Encrypted with AES-256-GCM — NOT plain text |
| `cuil` | Text | Encrypted with AES-256-GCM |
| `cbu` | Text | Encrypted with AES-256-GCM |
| `alias_cbu` | Text | Encrypted with AES-256-GCM |
| `banco` | String(100) | nullable |
| `regional` | String(100) | nullable |
| `legajo` | String(50) | nullable — business attribute, NOT identity |
| `legajo_profesional` | String(50) | nullable |
| `facturador` | Boolean | NOT NULL, default False |
| `estado` | String(20) | NOT NULL, default "Activo" |
| `created_at` | DateTime | via BaseModelMixin |
| `updated_at` | DateTime | via BaseModelMixin |
| `deleted_at` | DateTime | nullable, via BaseModelMixin |

**IMPORTANT — NO email field**: AuthUser (C-03) already has email for login. Email lives ONLY in AuthUser.

**PII encryption rules**:
- `dni`, `cuil`, `cbu`, `alias_cbu` SHALL be encrypted via `core/security.py` AES-256-GCM before storage
- Encrypted values SHALL be stored as base64-encoded strings in Text columns
- PII SHALL NEVER appear in plain text in database rows, log output, or API list responses
- Decryption SHALL only occur on explicit detail read (single entity by ID) with appropriate authorization
- The service layer SHALL handle encrypt/decrypt, not the model or repository

#### Scenario: Create usuario with valid fields
- **WHEN** creating a Usuario with nombre, apellidos, dni, cuil, cbu, alias_cbu, facturador, estado
- **THEN** the Usuario SHALL have a UUID id matching the AuthUser id, all provided fields, created_at, updated_at
- **AND** dni, cuil, cbu, alias_cbu SHALL be stored encrypted in the database

#### Scenario: Usuario 1:1 FK constraint
- **WHEN** creating a Usuario with an id that does not exist in auth_user
- **THEN** an IntegrityError SHALL be raised (FK constraint violation)

#### Scenario: Usuario default facturador
- **WHEN** creating a Usuario without specifying facturador
- **THEN** facturador SHALL default to False

#### Scenario: Usuario default estado
- **WHEN** creating a Usuario without specifying estado
- **THEN** estado SHALL default to "Activo"

#### Scenario: Usuario soft delete
- **WHEN** calling soft_delete on a Usuario
- **THEN** deleted_at SHALL be set to the current timestamp (not hard deleted)

#### Scenario: PII fields are encrypted in the database
- **WHEN** querying the usuario table directly (raw SQL)
- **THEN** dni, cuil, cbu, alias_cbu SHALL NOT be human-readable plain text

#### Scenario: PII decryption on read
- **WHEN** reading a Usuario by ID through the service layer
- **THEN** dni, cuil, cbu, alias_cbu SHALL be returned decrypted

### Requirement: UsuarioResponse and UsuarioSafeResponse schemas

The system SHALL provide two response schemas:

**UsuarioResponse** (full — with decrypted PII):
- id, tenant_id, nombre, apellidos, dni, cuil, cbu, alias_cbu, banco, regional, legajo, legajo_profesional, facturador, estado, created_at, updated_at
- `model_config = ConfigDict(from_attributes=True, extra='forbid')`

**UsuarioSafeResponse** (without PII — for lists and cross-references):
- id, tenant_id, nombre, apellidos, banco, regional, legajo, legajo_profesional, facturador, estado
- `model_config = ConfigDict(from_attributes=True, extra='forbid')`

#### Scenario: UsuarioSafeResponse excludes PII
- **WHEN** serializing a Usuario to UsuarioSafeResponse
- **THEN** fields dni, cuil, cbu, alias_cbu SHALL NOT be present

#### Scenario: UsuarioResponse includes all fields
- **WHEN** serializing a Usuario to UsuarioResponse
- **THEN** all fields including dni, cuil, cbu, alias_cbu SHALL be present

### Requirement: UsuarioRepository

The system SHALL provide a UsuarioRepository extending BaseRepository[Usuario] with:

- All BaseRepository methods (list, get, create, update, soft_delete)
- `get_by_legajo(legajo: str) -> Usuario | None` — find by legajo within tenant scope

#### Scenario: Get usuario by legajo
- **WHEN** calling get_by_legajo with an existing legajo in the tenant
- **THEN** the Usuario SHALL be returned

#### Scenario: Get usuario by legajo returns None for missing
- **WHEN** calling get_by_legajo with a non-existent legajo
- **THEN** None SHALL be returned

#### Scenario: Usuario list excludes soft-deleted
- **WHEN** calling list() after soft-deleting a Usuario
- **THEN** the result SHALL NOT include the soft-deleted Usuario

### Requirement: PII encryption helper integration

The system SHALL provide PII encryption integration in the UsuarioService:

- `create()` SHALL encrypt dni, cuil, cbu, alias_cbu before passing data to the repository
- `get()` SHALL NOT decrypt PII (returns UsuarioSafeResponse for list/get operations)
- `get_with_pii()` SHALL decrypt all PII fields before returning UsuarioResponse
- Encrypt/decrypt SHALL use `app.core.security.encrypt_value()` and `app.core.security.decrypt_value()`

#### Scenario: Encrypt before storage
- **WHEN** calling create on UsuarioService with plain text PII
- **THEN** the data passed to the repository SHALL have PII fields encrypted

#### Scenario: Decrypt on detail read
- **WHEN** calling get_with_pii on UsuarioService
- **THEN** the returned Usuario SHALL have PII fields decrypted to original values
