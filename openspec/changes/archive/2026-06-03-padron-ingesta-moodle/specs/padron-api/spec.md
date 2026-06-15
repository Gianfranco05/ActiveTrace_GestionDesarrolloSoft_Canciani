## ADDED Requirements

### Requirement: Padron API endpoints

The system SHALL provide the following API endpoints for padrón management:

| Method | Path | Guard | Description |
|--------|------|-------|-------------|
| POST | `/api/v1/padron/importar/preview` | `padron:cargar` | Upload file, return preview |
| POST | `/api/v1/padron/importar/confirmar` | `padron:cargar` | Confirm import, create version + entries |
| GET | `/api/v1/padron/versiones` | `padron:ver` | List versions, filterable by materia_id, cohorte_id |
| GET | `/api/v1/padron/versiones/{id}` | `padron:ver` | Get version detail |
| GET | `/api/v1/padron/versiones/{id}/entradas` | `padron:ver` | List entries for a version |
| POST | `/api/v1/padron/versiones/{id}/vaciar` | `padron:cargar` | Vaciar entries for a non-active version |

#### Scenario: POST /importar/preview returns preview
- **GIVEN** an authenticated user with permission `padron:cargar`
- **WHEN** uploading a valid .xlsx file
- **THEN** status SHALL be 200
- **AND** response SHALL contain filename, total_rows, preview_rows (default 20), detected_columns
- **AND** no data SHALL be persisted

#### Scenario: POST /importar/confirmar creates version
- **GIVEN** an authenticated user with permission `padron:cargar`
- **WHEN** sending a valid ImportConfirmRequest with file, materia_id, cohorte_id
- **THEN** status SHALL be 201
- **AND** response SHALL contain VersionPadronResponse with activa=True, entry count
- **AND** the previous active version (if exists) SHALL now have activa=False

#### Scenario: GET /versiones lists versions with pagination
- **GIVEN** multiple VersionPadrons for a given materia_id, cohorte_id
- **WHEN** calling GET /versiones?materia_id=X&cohorte_id=Y&offset=0&limit=10
- **THEN** status SHALL be 200
- **AND** response SHALL contain items, total, offset, limit
- **AND** items SHALL be VersionPadronResponse

#### Scenario: GET /versiones/{id}/entradas lists entries
- **GIVEN** a VersionPadron with 50 EntradaPadron entries
- **WHEN** calling GET /versiones/{id}/entradas?offset=0&limit=20
- **THEN** status SHALL be 200
- **AND** response SHALL contain items (EntradaPadronResponse), total=50

#### Scenario: POST /versiones/{id}/vaciar clears entries
- **GIVEN** a non-active VersionPadron with entries
- **WHEN** calling POST /versiones/{id}/vaciar
- **THEN** status SHALL be 200
- **AND** response SHALL contain version_id and entries_vaciadas count

#### Scenario: POST /versiones/{id}/vaciar fails for active version
- **GIVEN** an active VersionPadron
- **WHEN** calling POST /versiones/{id}/vaciar
- **THEN** status SHALL be 409
- **AND** detail SHALL indicate active version cannot be vaciado

#### Scenario: 403 without padron:cargar permission
- **GIVEN** an authenticated user WITHOUT `padron:cargar` permission
- **WHEN** calling POST /importar/preview
- **THEN** status SHALL be 403

#### Scenario: 401 without authentication
- **GIVEN** no authentication token
- **WHEN** calling any padron endpoint
- **THEN** status SHALL be 401

### Requirement: PadronRepository

The system SHALL provide a PadronRepository with the following methods:

| Method | Returns | Description |
|--------|---------|-------------|
| `create_version(data)` | `VersionPadron` | Create a new version |
| `get_active_version(materia_id, cohorte_id)` | `VersionPadron | None` | Get the active version for materia×cohorte |
| `deactivate_previous_active(materia_id, cohorte_id)` | `int` | Set activa=False for all active versions matching |
| `create_entries(version_id, entries)` | `list[EntradaPadron]` | Bulk create entries for a version |
| `get_entries(version_id, offset, limit)` | `tuple[list, int]` | Paginated entries for a version |
| `vaciar_entries(version_id)` | `int` | Soft-delete all entries for a version (returns count) |
| `list_versions(materia_id, cohorte_id, offset, limit)` | `tuple[list, int]` | Paginated versions |
| `get_version(version_id)` | `VersionPadron | None` | Get a single version |

#### Scenario: Create version persists correctly
- **GIVEN** valid version data
- **WHEN** calling create_version()
- **THEN** the version SHALL be persisted with a UUID id and timestamps

#### Scenario: Get active version returns correct version
- **GIVEN** two versions for same (materia, cohorte), one active, one not
- **WHEN** calling get_active_version()
- **THEN** the active version SHALL be returned

#### Scenario: Get active version returns None when none active
- **GIVEN** no active version for (materia, cohorte)
- **WHEN** calling get_active_version()
- **THEN** None SHALL be returned

#### Scenario: Deactivate previous active
- **GIVEN** an active version for (materia, cohorte)
- **WHEN** calling deactivate_previous_active()
- **THEN** the previous version's activa SHALL be set to False
- **AND** the count of updated rows SHALL be 1

#### Scenario: Vaciar entries returns correct count
- **GIVEN** a version with 100 entries
- **WHEN** calling vaciar_entries()
- **THEN** all 100 entries SHALL have deleted_at set
- **AND** the count returned SHALL be 100

#### Scenario: Tenant isolation in repository
- **GIVEN** versions and entries in two different tenants
- **WHEN** calling any repository method
- **THEN** results SHALL be scoped to the repository's tenant_id
