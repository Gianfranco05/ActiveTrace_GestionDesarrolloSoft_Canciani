## ADDED Requirements

### Requirement: VersionPadron ORM model

The system SHALL define a VersionPadron ORM model representing a versioned import of student rosters. The model SHALL extend BaseModelMixin (UUID PK, tenant_id FK, created_at, updated_at, deleted_at). The model SHALL record who imported the roster (cargado_por FK → Usuario) and when (cargado_at).

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK via BaseModelMixin |
| `tenant_id` | UUID | FK → Tenant via BaseModelMixin |
| `materia_id` | UUID | FK → Materia(id), NOT NULL |
| `cohorte_id` | UUID | FK → Cohorte(id), NOT NULL |
| `cargado_por` | UUID | FK → Usuario(id), NOT NULL — who imported |
| `cargado_at` | DateTime | NOT NULL, default utcnow |
| `activa` | Boolean | NOT NULL, default True |
| `created_at` | DateTime | via BaseModelMixin |
| `updated_at` | DateTime | via BaseModelMixin |
| `deleted_at` | DateTime | nullable, via BaseModelMixin |

**IMPORTANT — One active version per (tenant_id, materia_id, cohorte_id)**: A partial unique index SHALL enforce this at the DB level: `UNIQUE (tenant_id, materia_id, cohorte_id) WHERE activa = true AND deleted_at IS NULL`.

#### Scenario: Create version padron with valid fields
- **GIVEN** a valid materia_id, cohorte_id, and cargado_por (existing Usuario)
- **WHEN** creating a VersionPadron with all required fields
- **THEN** the VersionPadron SHALL have a UUID id, all provided fields, cargado_at set to current timestamp, activa=True, created_at, updated_at

#### Scenario: Activating new version deactivates previous
- **GIVEN** an existing VersionPadron with activa=True for (tenant_id, materia_id, cohorte_id)
- **WHEN** a new VersionPadron is created with activa=True for the same (tenant_id, materia_id, cohorte_id)
- **THEN** the previous VersionPadron's activa SHALL be set to False
- **AND** the new VersionPadron SHALL have activa=True

#### Scenario: Unique constraint prevents two active versions
- **GIVEN** an existing VersionPadron with activa=True for (tenant_id, materia_id, cohorte_id)
- **WHEN** attempting to create a second VersionPadron with activa=True for the same triple WITHOUT deactivating the first
- **THEN** a DB integrity error SHALL be raised (unique constraint violation)

#### Scenario: Multiple inactive versions allowed
- **GIVEN** two VersionPadrons for the same (tenant_id, materia_id, cohorte_id), both with activa=False
- **WHEN** querying versions for that triple
- **THEN** both versions SHALL be returned

#### Scenario: VersionPadron with non-existent materia
- **WHEN** creating a VersionPadron with a materia_id that does not exist
- **THEN** an IntegrityError SHALL be raised (FK constraint violation)

#### Scenario: VersionPadron soft delete is independent
- **GIVEN** a VersionPadron with activa=True
- **WHEN** calling soft_delete on the VersionPadron
- **THEN** deleted_at SHALL be set
- **AND** the unique constraint SHALL NOT prevent creating a new active version (the deleted one is excluded by the partial index)

#### Scenario: Tenant isolation
- **GIVEN** VersionPadrons in two different tenants
- **WHEN** querying versions filtered by tenant_id
- **THEN** only versions belonging to that tenant SHALL be returned
