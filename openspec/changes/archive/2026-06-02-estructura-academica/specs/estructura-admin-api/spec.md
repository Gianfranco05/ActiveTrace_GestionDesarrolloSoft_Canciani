## ADDED Requirements

### Requirement: CRUD endpoints for Carrera
The system SHALL provide REST endpoints for managing Carreras under `/api/v1/estructura/carreras`.

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/api/v1/estructura/carreras` | `estructura:gestionar` | List all non-deleted carreras, filterable by estado |
| POST | `/api/v1/estructura/carreras` | `estructura:gestionar` | Create a new carrera |
| GET | `/api/v1/estructura/carreras/{id}` | `estructura:gestionar` | Get a single carrera |
| PUT | `/api/v1/estructura/carreras/{id}` | `estructura:gestionar` | Update a carrera |
| DELETE | `/api/v1/estructura/carreras/{id}` | `estructura:gestionar` | Soft-delete a carrera |

Request body for POST: `CarreraCreate(codigo, nombre, estado?)`.
Request body for PUT: `CarreraUpdate(codigo?, nombre?, estado?)`.
Response: `CarreraResponse`.

#### Scenario: List carreras returns paginated results
- **WHEN** a user with `estructura:gestionar` permission calls GET /api/v1/estructura/carreras
- **THEN** a paginated list of CarreraResponse SHALL be returned, scoped to the user's tenant

#### Scenario: Create carrera succeeds
- **WHEN** a user with permission sends a valid CarreraCreate body
- **THEN** a CarreraResponse with the created entity SHALL be returned (201)

#### Scenario: Create duplicate codigo returns 409
- **WHEN** a user sends a CarreraCreate with a codigo that already exists in the tenant
- **THEN** HTTP 409 Conflict SHALL be returned

#### Scenario: Create carrera without permission returns 403
- **WHEN** a user WITHOUT `estructura:gestionar` permission sends a POST
- **THEN** HTTP 403 Forbidden SHALL be returned

#### Scenario: Update carrera
- **WHEN** a user with permission sends a CarreraUpdate with nombre and estado
- **THEN** the carrera SHALL be updated and the response SHALL reflect the changes

#### Scenario: Soft delete carrera
- **WHEN** a user with permission sends DELETE /api/v1/estructura/carreras/{id}
- **THEN** the carrera SHALL be soft-deleted (deleted_at set, NOT hard deleted)

### Requirement: CRUD endpoints for Cohorte
The system SHALL provide REST endpoints for managing Cohorte under `/api/v1/estructura/cohortes`.

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/api/v1/estructura/cohortes` | `estructura:gestionar` | List all non-deleted cohortes, filterable by carrera_id and estado |
| POST | `/api/v1/estructura/cohortes` | `estructura:gestionar` | Create a new cohorte |
| GET | `/api/v1/estructura/cohortes/{id}` | `estructura:gestionar` | Get a single cohorte |
| PUT | `/api/v1/estructura/cohortes/{id}` | `estructura:gestionar` | Update a cohorte |
| DELETE | `/api/v1/estructura/cohortes/{id}` | `estructura:gestionar` | Soft-delete a cohorte |

#### Scenario: List cohortes filtered by carrera_id
- **WHEN** calling GET /api/v1/estructura/cohortes?carrera_id=<uuid>
- **THEN** only cohortes for that carrera SHALL be returned

#### Scenario: Create cohorte with inactive carrera returns 409
- **WHEN** creating a Cohorte for a Carrera with estado "Inactiva"
- **THEN** HTTP 409 Conflict SHALL be returned with detail "Carrera must be active to create cohortes"

#### Scenario: Create cohorte with active carrera succeeds (201)
- **WHEN** creating a Cohorte for a Carrera with estado "Activa"
- **THEN** HTTP 201 Created SHALL be returned

### Requirement: CRUD endpoints for Materia
The system SHALL provide REST endpoints for managing Materias under `/api/v1/estructura/materias`.

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/api/v1/estructura/materias` | `estructura:gestionar` | List all non-deleted materias, filterable by estado |
| POST | `/api/v1/estructura/materias` | `estructura:gestionar` | Create a new materia |
| GET | `/api/v1/estructura/materias/{id}` | `estructura:gestionar` | Get a single materia |
| PUT | `/api/v1/estructura/materias/{id}` | `estructura:gestionar` | Update a materia |
| DELETE | `/api/v1/estructura/materias/{id}` | `estructura:gestionar` | Soft-delete a materia |

#### Scenario: List materias returns paginated results
- **WHEN** a user with permission calls GET /api/v1/estructura/materias
- **THEN** a paginated list of MateriaResponse SHALL be returned

#### Scenario: Create materia succeeds
- **WHEN** a user with permission sends a valid MateriaCreate body
- **THEN** a MateriaResponse with HTTP 201 SHALL be returned

#### Scenario: Create materia without permission returns 403
- **WHEN** a user without `estructura:gestionar` sends a POST
- **THEN** HTTP 403 Forbidden SHALL be returned

### Requirement: 401 before 403
The system SHALL return HTTP 401 (Not authenticated) before HTTP 403 (Forbidden). Authentication failure takes precedence over authorization.

#### Scenario: Unauthenticated user receives 401
- **WHEN** a request without a valid JWT accesses any estructura endpoint
- **THEN** HTTP 401 Unauthorized SHALL be returned
