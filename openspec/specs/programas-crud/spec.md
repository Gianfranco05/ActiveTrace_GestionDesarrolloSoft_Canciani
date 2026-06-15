# programas-crud Specification

## Purpose
Subir, listar y gestionar los programas oficiales de cada materia para una combinación de carrera y cohorte. El archivo se almacena con referencia opaca; el backend no interpreta su contenido.

## ADDED Requirements

### Requirement: Subir y asociar programa de materia (F5.3)

The system SHALL allow ADMIN and COORDINADOR to upload a program document and associate it to a materia × carrera × cohorte combination. The file SHALL be delegated to the storage service and only an opaque reference string SHALL be persisted.

- Method: POST
- Path: `/api/programas`
- Guard: `require_permission("estructura:gestionar")`
- Request: `multipart/form-data` with `archivo` (file, required), `materia_id` (UUID, required), `carrera_id` (UUID, required), `cohorte_id` (UUID, required), `titulo` (str, required, max 300)
- Response 201: `ProgramaMateriaResponse` with `id`, `materia_id`, `carrera_id`, `cohorte_id`, `titulo`, `referencia_archivo`, `cargado_at`
- The system SHALL validate that materia_id, carrera_id, and cohorte_id exist and belong to the tenant (404 if any is missing)
- The system SHALL reject empty files (422 if 0 bytes)
- The system SHALL audit the operation with `PROGRAMA_SUBIR`
- The system SHALL NOT interpret or validate the file content — only the opaque reference is stored

#### Scenario: Subir programa exitoso
- **WHEN** an ADMIN sends POST /api/programas with a valid PDF file, materia_id, carrera_id, cohorte_id, and titulo "Programa Analítico 2026"
- **THEN** the system SHALL store the file via the storage service and obtain a reference
- **AND** the system SHALL create a ProgramaMateria record with `referencia_archivo` set to the opaque reference
- **AND** the system SHALL respond 201 with ProgramaMateriaResponse

#### Scenario: Subir programa con materia inexistente
- **WHEN** an ADMIN sends POST /api/programas with a non-existent materia_id
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Subir programa con archivo vacío
- **WHEN** an ADMIN sends POST /api/programas with a 0-byte file
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Subir programa sin permisos
- **WHEN** a user without `estructura:gestionar` sends POST /api/programas
- **THEN** the system SHALL respond 403 Forbidden

#### Scenario: Subir programa con tenant isolation
- **WHEN** an ADMIN of tenant A sends POST with a materia_id that belongs to tenant B
- **THEN** the system SHALL respond 404 Not Found

### Requirement: Listar programas de materias (F5.3)

The system SHALL provide an endpoint to list ProgramaMateria records with optional filters.

- Method: GET
- Path: `/api/programas`
- Guard: `require_permission("estructura:gestionar")`
- Query params: `materia_id` (UUID?, optional), `carrera_id` (UUID?, optional), `cohorte_id` (UUID?, optional), `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response 200: `{"items": list[ProgramaMateriaResponse], "total": int, "offset": int, "limit": int}`
- Results SHALL be filtered by tenant_id automatically
- Soft-deleted records (deleted_at IS NOT NULL) SHALL be excluded by default

#### Scenario: Listar todos los programas del tenant
- **WHEN** a COORDINADOR calls GET /api/programas without filters
- **THEN** the system SHALL return all non-deleted ProgramaMateria records for the tenant

#### Scenario: Listar programas filtrados por materia
- **WHEN** calling GET /api/programas?materia_id=<uuid>
- **THEN** the system SHALL return only programs for that materia

#### Scenario: Listar programas combinando filtros
- **WHEN** calling GET /api/programas?materia_id=<uuid>&cohorte_id=<uuid>
- **THEN** the system SHALL return only programs matching both filters

#### Scenario: Listar programas devuelve vacío
- **WHEN** a materia has no programs and GET /api/programas?materia_id=<uuid> is called
- **THEN** the system SHALL return an empty items list with total=0

#### Scenario: Listar programas sin permisos
- **WHEN** a user without `estructura:gestionar` calls GET /api/programas
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Consultar programa de materia por ID (F5.3)

The system SHALL allow retrieving a single ProgramaMateria by its ID.

- Method: GET
- Path: `/api/programas/{id}`
- Guard: `require_permission("estructura:gestionar")`
- Response 200: `ProgramaMateriaResponse`
- The system SHALL return 404 if the record does not exist, is soft-deleted, or belongs to a different tenant

#### Scenario: Consultar programa existente
- **WHEN** a COORDINADOR calls GET /api/programas/<id> for an existing program
- **THEN** the system SHALL return the complete ProgramaMateriaResponse including `referencia_archivo`

#### Scenario: Consultar programa inexistente
- **WHEN** GET /api/programas/<id> is called with a non-existent UUID
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Consultar programa soft-deleted
- **WHEN** GET /api/programas/<id> is called for a program that was soft-deleted
- **THEN** the system SHALL respond 404 Not Found

### Requirement: Eliminar programa de materia (soft delete, F5.3)

The system SHALL allow soft-deleting a ProgramaMateria. The file in the storage service SHALL NOT be affected.

- Method: DELETE
- Path: `/api/programas/{id}`
- Guard: `require_permission("estructura:gestionar")`
- Response 204: No Content
- The record SHALL be soft-deleted (deleted_at timestamp set)
- The storage service file SHALL remain untouched — the reference is preserved for audit

#### Scenario: Eliminar programa exitoso
- **WHEN** a COORDINADOR sends DELETE /api/programas/<id> for an existing program
- **THEN** the program SHALL be soft-deleted (deleted_at set)
- **AND** the system SHALL respond 204 No Content
- **AND** subsequent GET /api/programas/<id> SHALL return 404

#### Scenario: Eliminar programa ya eliminado
- **WHEN** DELETE /api/programas/<id> is called for an already soft-deleted program
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Eliminar programa sin permisos
- **WHEN** a user without `estructura:gestionar` sends DELETE /api/programas/<id>
- **THEN** the system SHALL respond 403 Forbidden
