## ADDED Requirements

### Requirement: EntradaPadron ORM model

The system SHALL define an EntradaPadron ORM model representing an individual student entry within a versioned roster. The model SHALL extend BaseModelMixin (UUID PK, tenant_id FK, timestamps, soft delete). The model SHALL reference a VersionPadron and optionally reference a Usuario (for students who already have accounts).

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK via BaseModelMixin |
| `tenant_id` | UUID | FK → Tenant via BaseModelMixin |
| `version_id` | UUID | FK → VersionPadron(id), NOT NULL |
| `usuario_id` | UUID | FK → Usuario(id), NULLABLE |
| `nombre` | String(100) | Denormalized, NOT NULL |
| `apellidos` | String(150) | Denormalized, NOT NULL |
| `email` | Text | Encrypted via EncryptedString TypeDecorator |
| `comision` | String(50) | nullable |
| `regional` | String(100) | nullable |

**IMPORTANT — usuario_id nullable**: EntradaPadron can exist BEFORE the student has a Usuario account. This enables importing rosters from Moodle or files before students register in the system.

**IMPORTANT — Denormalized fields**: `nombre` and `apellidos` SHALL store the value as present at import time, even if the Usuario later changes their name. This preserves historical accuracy for grade records (C-10).

#### Scenario: Create entrada padron with valid fields
- **GIVEN** an existing VersionPadron
- **WHEN** creating an EntradaPadron with nombre, apellidos, email (plain text), comision, regional
- **THEN** the EntradaPadron SHALL have a UUID id, version_id, all provided fields, created_at
- **AND** email SHALL be stored encrypted in the database

#### Scenario: Entrada padron with nullable usuario_id
- **WHEN** creating an EntradaPadron without usuario_id
- **THEN** usuario_id SHALL be NULL

#### Scenario: Entrada padron with linked usuario
- **GIVEN** an existing Usuario
- **WHEN** creating an EntradaPadron with that usuario_id
- **THEN** usuario_id SHALL reference the existing Usuario

#### Scenario: Email is auto-encrypted on write
- **WHEN** querying the entrada_padron table directly (raw SQL)
- **THEN** the email column SHALL NOT be human-readable plain text

#### Scenario: Email is auto-decrypted on ORM read
- **WHEN** reading an EntradaPadron through the ORM
- **THEN** the email field SHALL contain the plain text original value

#### Scenario: Entrada padron FK to non-existent version
- **WHEN** creating an EntradaPadron with a version_id that does not exist
- **THEN** an IntegrityError SHALL be raised

#### Scenario: Multiple entries per version are allowed
- **GIVEN** a VersionPadron
- **WHEN** creating multiple EntradaPadron rows for the same version
- **THEN** all entries SHALL be persisted and queryable

#### Scenario: Entrada padron soft delete
- **WHEN** calling soft_delete on an EntradaPadron
- **THEN** deleted_at SHALL be set (not hard deleted)

#### Scenario: Entrada padron list excludes soft-deleted
- **WHEN** listing EntradaPadron for a VersionPadron after soft-deleting some entries
- **THEN** soft-deleted entries SHALL NOT appear in results

#### Scenario: Tenant isolation
- **GIVEN** EntradaPadrons in two different tenants
- **WHEN** querying entries filtered by tenant_id
- **THEN** only entries belonging to that tenant SHALL be returned
