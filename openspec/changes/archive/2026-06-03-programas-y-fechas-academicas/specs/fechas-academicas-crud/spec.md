# fechas-academicas-crud Specification

## Purpose
CRUD completo de fechas académicas (parciales, TPs, coloquios, recuperatorios) por materia y cohorte, con listado tabular y vista tipo calendario.

## ADDED Requirements

### Requirement: Crear fecha académica (F5.4)

The system SHALL allow COORDINADOR and ADMIN to register an evaluation date for a materia × cohorte combination.

- Method: POST
- Path: `/api/fechas-academicas`
- Guard: `require_permission("estructura:gestionar")`
- Request body: `FechaAcademicaCreateRequest` with `materia_id` (UUID, required), `cohorte_id` (UUID, required), `tipo` (str, required, enum: Parcial, TP, Coloquio, Recuperatorio), `numero` (int, required, >= 1), `periodo` (str, required, max 20), `fecha` (date, required), `titulo` (str?, optional, max 200)
- Response 201: `FechaAcademicaResponse` with `id`, `materia_id`, `cohorte_id`, `tipo`, `numero`, `periodo`, `fecha`, `titulo`
- The system SHALL validate that materia_id and cohorte_id exist and belong to the tenant (404 if missing)
- The system SHALL audit with `FECHA_ACADEMICA_MODIFICAR`
- Multiple records with the same materia × cohorte × tipo × numero SHALL be allowed (for rescheduled dates)

#### Scenario: Crear fecha de parcial exitosa
- **WHEN** a COORDINADOR sends POST /api/fechas-academicas with `tipo: Parcial`, `numero: 1`, `periodo: "2026-1"`, `fecha: "2026-04-15"`, `titulo: "Primer Parcial"`
- **THEN** the system SHALL create a FechaAcademica record and respond 201

#### Scenario: Crear fecha con materia inexistente
- **WHEN** POST /api/fechas-academicas is sent with a non-existent materia_id
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Crear fecha con numero inválido
- **WHEN** POST /api/fechas-academicas is sent with `numero: 0`
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Crear fecha con tipo inválido
- **WHEN** POST /api/fechas-academicas is sent with `tipo: "ExamenFinal"`
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Crear fecha sin permisos
- **WHEN** a user without `estructura:gestionar` sends POST /api/fechas-academicas
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Listar fechas académicas (tabular, F5.4)

The system SHALL provide a paginated list of FechaAcademica records with multiple filters.

- Method: GET
- Path: `/api/fechas-academicas`
- Guard: `require_permission("estructura:gestionar")`
- Query params: `materia_id` (UUID?, optional), `cohorte_id` (UUID?, optional), `tipo` (str?, optional: Parcial, TP, Coloquio, Recuperatorio), `periodo` (str?, optional), `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response 200: `{"items": list[FechaAcademicaResponse], "total": int, "offset": int, "limit": int}`
- Results SHALL be ordered by fecha ASC
- Soft-deleted records SHALL be excluded

#### Scenario: Listar todas las fechas del tenant
- **WHEN** an ADMIN calls GET /api/fechas-academicas without filters
- **THEN** the system SHALL return all non-deleted FechaAcademica records ordered by fecha ASC

#### Scenario: Listar fechas filtradas por materia y periodo
- **WHEN** calling GET /api/fechas-academicas?materia_id=<uuid>&periodo=2026-1
- **THEN** the system SHALL return only fechas for that materia in that period

#### Scenario: Listar fechas filtradas por tipo
- **WHEN** calling GET /api/fechas-academicas?tipo=Parcial
- **THEN** the system SHALL return only records with tipo "Parcial"

#### Scenario: Listar fechas devuelve vacío
- **WHEN** no fechas match the filters
- **THEN** the system SHALL return an empty items list with total=0

#### Scenario: Listar fechas con paginación
- **WHEN** calling GET /api/fechas-academicas?offset=0&limit=5 with 12 total records
- **THEN** the system SHALL return 5 items and total=12

### Requirement: Vista calendario de fechas académicas (F5.4)

The system SHALL provide a flat, chronologically ordered list of FechaAcademica records for calendar rendering.

- Method: GET
- Path: `/api/fechas-academicas/calendario`
- Guard: `require_permission("estructura:gestionar")`
- Query params: `materia_id` (UUID?, optional), `cohorte_id` (UUID?, optional), `periodo` (str?, optional), `fecha_desde` (date?, optional), `fecha_hasta` (date?, optional)
- Response 200: `{"items": list[FechaAcademicaResponse], "total": int}`
- Results SHALL be ordered by fecha ASC
- Calendar view SHALL NOT paginate — it returns all matching records for the given scope
- Soft-deleted records SHALL be excluded

#### Scenario: Calendario de una materia y cohorte específicas
- **WHEN** calling GET /api/fechas-academicas/calendario?materia_id=<uuid>&cohorte_id=<uuid>
- **THEN** the system SHALL return all fechas for that materia × cohorte ordered by fecha ASC

#### Scenario: Calendario con rango de fechas
- **WHEN** calling GET /api/fechas-academicas/calendario?fecha_desde=2026-04-01&fecha_hasta=2026-04-30
- **THEN** the system SHALL return only fechas within the specified date range

#### Scenario: Calendario sin fechas
- **WHEN** no fechas match the calendar filters
- **THEN** the system SHALL return an empty items list with total=0

#### Scenario: Calendario sin permisos
- **WHEN** a user without `estructura:gestionar` calls GET /api/fechas-academicas/calendario
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Editar fecha académica (F5.4)

The system SHALL allow partial update of a FechaAcademica record.

- Method: PATCH
- Path: `/api/fechas-academicas/{id}`
- Guard: `require_permission("estructura:gestionar")`
- Request body: `FechaAcademicaUpdateRequest` with optional fields: `tipo`, `numero`, `periodo`, `fecha`, `titulo`
- Response 200: `FechaAcademicaResponse` with updated fields
- Only the fields present in the request SHALL be updated (partial update)
- The system SHALL audit with `FECHA_ACADEMICA_MODIFICAR`
- The system SHALL return 404 if the record does not exist, is soft-deleted, or belongs to a different tenant

#### Scenario: Editar solo la fecha
- **WHEN** a COORDINADOR sends PATCH /api/fechas-academicas/<id> with `fecha: "2026-05-01"`
- **THEN** only the fecha field SHALL be updated; all other fields remain unchanged

#### Scenario: Editar múltiples campos
- **WHEN** PATCH is sent with `tipo: "Coloquio"` and `titulo: "Coloquio Integrador"`
- **THEN** both tipo and titulo SHALL be updated

#### Scenario: Editar fecha inexistente
- **WHEN** PATCH /api/fechas-academicas/<id> is called with a non-existent UUID
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Editar fecha sin permisos
- **WHEN** a user without `estructura:gestionar` sends PATCH /api/fechas-academicas/<id>
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Eliminar fecha académica (soft delete, F5.4)

The system SHALL allow soft-deleting a FechaAcademica record.

- Method: DELETE
- Path: `/api/fechas-academicas/{id}`
- Guard: `require_permission("estructura:gestionar")`
- Response 204: No Content
- The record SHALL be soft-deleted (deleted_at timestamp set)
- The system SHALL audit with `FECHA_ACADEMICA_MODIFICAR`

#### Scenario: Eliminar fecha exitosa
- **WHEN** a COORDINADOR sends DELETE /api/fechas-academicas/<id> for an existing record
- **THEN** the record SHALL be soft-deleted and the system SHALL respond 204

#### Scenario: Eliminar fecha ya eliminada
- **WHEN** DELETE is called for an already soft-deleted record
- **THEN** the system SHALL respond 404 Not Found
