# avisos-crud Specification

## Purpose
ABM de avisos del sistema (F3.5). Crear, editar, soft-delete y consultar avisos por COORDINADOR/ADMIN. Define los endpoints de gestión del tablón de avisos institucionales.

## ADDED Requirements

### Requirement: Crear aviso (F3.5, FL-09 paso 1-2)
The system SHALL allow COORDINADOR and ADMIN to create a new Aviso with configurable scope, severity, visibility window, priority, and acknowledgment requirement.

- Method: POST
- Path: `/api/avisos`
- Guard: `require_permission("avisos:publicar")`
- Request body: `AvisoCreateRequest` with `alcance` (enum: Global, PorMateria, PorCohorte, PorRol, required), `materia_id` (UUID?, nullable — required if alcance=PorMateria), `cohorte_id` (UUID?, nullable — required if alcance=PorCohorte), `rol_destino` (enum?, nullable — required if alcance=PorRol, ignored otherwise), `severidad` (enum: Info, Advertencia, Critico, required), `titulo` (str, required, max 200), `cuerpo` (str, required), `inicio_en` (datetime, required), `fin_en` (datetime, required), `orden` (int, default 0), `activo` (bool, default true), `requiere_ack` (bool, default false)
- Response 201: `AvisoResponse` with all fields
- The system SHALL validate `inicio_en` < `fin_en`; if not, respond 422
- The system SHALL validate that if `alcance=PorMateria`, `materia_id` must be provided and must exist in the tenant; if missing or invalid, respond 422
- The system SHALL validate that if `alcance=PorCohorte`, `cohorte_id` must be provided and must exist in the tenant; if missing or invalid, respond 422
- The system SHALL validate that if `alcance=PorRol`, `rol_destino` must be provided with a valid role enum value; if missing or invalid, respond 422
- The system SHALL audit the operation with `AVISO_PUBLICAR`

#### Scenario: Crear aviso global exitoso
- **WHEN** a COORDINADOR sends POST /api/avisos with `alcance: Global`, `titulo: "Bienvenida"`, `inicio_en: 2026-06-01T00:00:00Z`, `fin_en: 2026-12-31T23:59:59Z`
- **THEN** the system SHALL create the Aviso and respond 201 with the created data including tenant_id and a generated UUID id
- **AND** the aviso SHALL have `activo: true` by default
- **AND** the aviso SHALL have `requiere_ack: false` by default
- **AND** the system SHALL generate an audit log entry with code `AVISO_PUBLICAR`

#### Scenario: Crear aviso con requiere_ack
- **WHEN** a COORDINADOR sends POST /api/avisos with `alcance: Global`, `requiere_ack: true`
- **THEN** the system SHALL create the Aviso with `requiere_ack: true`

#### Scenario: Crear aviso con inicio posterior a fin
- **WHEN** a COORDINADOR sends POST /api/avisos with `inicio_en: 2026-12-01T00:00:00Z`, `fin_en: 2026-01-01T00:00:00Z`
- **THEN** the system SHALL respond 422 Unprocessable Entity with a validation error

#### Scenario: Crear aviso PorMateria sin materia_id
- **WHEN** a COORDINADOR sends POST /api/avisos with `alcance: PorMateria` but `materia_id: null`
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Crear aviso PorCohorte sin cohorte_id
- **WHEN** a COORDINADOR sends POST /api/avisos with `alcance: PorCohorte` but `cohorte_id: null`
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Crear aviso PorRol sin rol_destino
- **WHEN** a COORDINADOR sends POST /api/avisos with `alcance: PorRol` but `rol_destino: null`
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Crear aviso sin permisos
- **WHEN** a user without `avisos:publicar` sends POST /api/avisos
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Editar aviso
The system SHALL allow COORDINADOR and ADMIN to update an existing Aviso. All fields except `id` and `tenant_id` SHALL be updatable.

- Method: PUT
- Path: `/api/avisos/{aviso_id}`
- Guard: `require_permission("avisos:publicar")`
- Request body: `AvisoUpdateRequest` — all fields optional, same types as create, `model_config = ConfigDict(extra='forbid')`
- Response 200: `AvisoResponse` with updated fields
- The system SHALL validate `inicio_en` < `fin_en` if both are provided
- The system SHALL validate `materia_id` exists in tenant if provided with `alcance=PorMateria`
- The system SHALL validate `cohorte_id` exists in tenant if provided with `alcance=PorCohorte`
- The system SHALL return 404 if the aviso does not exist or is soft-deleted
- The system SHALL audit the operation with `AVISO_MODIFICAR`

#### Scenario: Editar aviso existente
- **WHEN** a COORDINADOR sends PUT /api/avisos/{id} with `titulo: "Actualizado"` and `activo: false`
- **THEN** the system SHALL update only the provided fields and respond 200 with the full updated AvisoResponse

#### Scenario: Editar aviso inexistente
- **WHEN** a COORDINADOR sends PUT /api/avisos/{non-existent-id}
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Editar aviso soft-deleted
- **WHEN** a COORDINADOR sends PUT /api/avisos/{id} where the aviso has `deleted_at IS NOT NULL`
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Editar aviso sin permisos
- **WHEN** a user without `avisos:publicar` sends PUT /api/avisos/{id}
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Soft-delete aviso
The system SHALL allow COORDINADOR and ADMIN to soft-delete an Aviso. Soft-deleted avisos SHALL not appear in any listing endpoint.

- Method: DELETE
- Path: `/api/avisos/{aviso_id}`
- Guard: `require_permission("avisos:publicar")`
- Response 204: No Content
- The system SHALL return 404 if the aviso does not exist or is already soft-deleted
- The system SHALL audit the operation with `AVISO_ELIMINAR`

#### Scenario: Soft-delete aviso existente
- **WHEN** a COORDINADOR sends DELETE /api/avisos/{id}
- **THEN** the system SHALL set `deleted_at` to the current timestamp and respond 204
- **AND** the aviso SHALL no longer appear in aviso listing or detail endpoints
- **AND** the system SHALL generate an audit log entry with code `AVISO_ELIMINAR`

#### Scenario: Soft-delete aviso ya eliminado
- **WHEN** a COORDINADOR sends DELETE /api/avisos/{id} where the aviso already has `deleted_at IS NOT NULL`
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Soft-delete aviso inexistente
- **WHEN** a COORDINADOR sends DELETE /api/avisos/{non-existent-id}
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Soft-delete aviso sin permisos
- **WHEN** a user without `avisos:publicar` sends DELETE /api/avisos/{id}
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Obtener detalle de aviso por ID
The system SHALL allow any authenticated user to retrieve a single Aviso by its ID.

- Method: GET
- Path: `/api/avisos/{aviso_id}`
- Guard: `require_authenticated` (any authenticated user)
- Response 200: `AvisoDetailResponse` with all aviso fields plus `acknowledged: bool` (whether the current user has confirmed this aviso)
- The system SHALL return 404 if the aviso does not exist, is soft-deleted, or is not visible to the user (outside vigencia, wrong scope)
- The system SHALL NOT require the aviso to be within the visibility window for detail retrieval (admins may need to preview before publishing)

#### Scenario: Obtener detalle de aviso activo
- **WHEN** an authenticated user sends GET /api/avisos/{id}
- **THEN** the system SHALL respond 200 with the AvisoDetailResponse including `acknowledged: bool`

#### Scenario: Obtener detalle de aviso inexistente
- **WHEN** an authenticated user sends GET /api/avisos/{non-existent-id}
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Obtener detalle sin autenticación
- **WHEN** an unauthenticated request sends GET /api/avisos/{id}
- **THEN** the system SHALL respond 401 Unauthorized
