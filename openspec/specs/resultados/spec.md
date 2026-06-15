# resultados Specification

## Purpose
TBD - created by archiving change evaluaciones-y-coloquios. Update Purpose after archive.
## Requirements
### Requirement: POST /api/coloquios/{id}/resultados — registrar resultado de evaluación (F7.5)

The system SHALL allow COORDINADOR/ADMIN to record a final grade for a student in an evaluation.

- Method: POST
- Path: `/api/coloquios/{id}/resultados`
- Guard: `require_permission("coloquios:gestionar")`
- Request body: ResultadoRequest
  - `alumno_id` (UUID, required)
  - `nota_final` (str, required, min 1, max 50)
  - `model_config = ConfigDict(extra='forbid')`
- Response: 201 Created with ResultadoResponse
- The endpoint SHALL validate the evaluation exists
- The endpoint SHALL validate the alumno exists and belongs to the tenant
- If a result already exists for the same (evaluacion_id, alumno_id), the new nota_final SHALL replace the previous one (upsert)
- The endpoint SHALL generate audit `COLOQUIO_RESULTADO`

#### Scenario: Registrar resultado exitoso
- **WHEN** calling POST /api/coloquios/{id}/resultados with valid alumno_id and nota_final
- **THEN** 201 Created SHALL be returned with the ResultadoResponse

#### Scenario: Registrar resultado reemplaza anterior
- **WHEN** calling POST /api/coloquios/{id}/resultados for an alumno that already has a result in the same evaluation
- **THEN** the existing nota_final SHALL be updated with the new value
- **AND** 200 OK SHALL be returned

#### Scenario: Registrar resultado rechaza alumno inexistente
- **WHEN** calling POST /api/coloquios/{id}/resultados with a non-existent alumno_id
- **THEN** 404 Not Found SHALL be returned

#### Scenario: Registrar resultado rechaza evaluación inexistente
- **WHEN** calling POST /api/coloquios/{id}/resultados with a non-existent evaluation id
- **THEN** 404 Not Found SHALL be returned

#### Scenario: Registrar resultado genera auditoría
- **WHEN** a result is registered successfully
- **THEN** an AuditLog entry with action "COLOQUIO_RESULTADO" SHALL be created

### Requirement: GET /api/coloquios/{id}/resultados — listar resultados de una evaluación (F7.5)

The system SHALL provide the list of all recorded results for a specific evaluation.

- Method: GET
- Path: `/api/coloquios/{id}/resultados`
- Guard: `require_permission("coloquios:gestionar")`
- Query params: `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[ResultadoResponse], "total": int, "offset": int, "limit": int}`
- Each item SHALL include alumno_nombre, alumno_apellidos, nota_final

#### Scenario: Listar resultados con datos
- **WHEN** calling GET /api/coloquios/{id}/resultados for an evaluation with recorded results
- **THEN** a paginated list of ResultadoResponse items SHALL be returned

#### Scenario: Listar resultados vacío
- **WHEN** calling GET /api/coloquios/{id}/resultados for an evaluation with no results
- **THEN** an empty list SHALL be returned

### Requirement: GET /api/coloquios/admin/consolidado — registro académico consolidado (F7.5)

The system SHALL provide COORDINADOR/ADMIN with a consolidated academic record of all evaluation results across the tenant.

- Method: GET
- Path: `/api/coloquios/admin/consolidado`
- Guard: `require_permission("coloquios:gestionar")`
- Query params: `materia_id` (UUID?, filter), `cohorte_id` (UUID?, filter), `alumno_id` (UUID?, filter by alumno), `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[ConsolidadoResponse], "total": int, "offset": int, "limit": int}`
- Results SHALL include alumno_id, alumno_nombre, alumno_apellidos, materia_nombre, instancia, nota_final, fecha_registro
- Results SHALL be ordered by alumno_apellidos ascending, then materia_nombre

#### Scenario: Consolidado filtrado por materia
- **WHEN** calling GET /api/coloquios/admin/consolidado?materia_id=<uuid>
- **THEN** only results for evaluations of that materia SHALL be returned

#### Scenario: Consolidado filtrado por alumno
- **WHEN** calling GET /api/coloquios/admin/consolidado?alumno_id=<uuid>
- **THEN** only results for that specific alumno SHALL be returned

#### Scenario: Consolidado vacío sin resultados
- **WHEN** calling GET /api/coloquios/admin/consolidado with no results in the tenant
- **THEN** an empty list SHALL be returned

### Requirement: GET /api/coloquios/admin/convocatorias — administración global de convocatorias (F7.5)

The system SHALL provide ADMIN with a comprehensive view of all evaluations including soft-deleted ones, with full management capabilities.

- Method: GET
- Path: `/api/coloquios/admin/convocatorias`
- Guard: `require_permission("coloquios:gestionar")`
- Query params: `materia_id` (UUID?, filter), `cohorte_id` (UUID?, filter), `tipo` (str?, filter), `incluir_inactivas` (bool?, default false), `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[EvaluacionResponse], "total": int, "offset": int, "limit": int}`
- When `incluir_inactivas=true`, the endpoint SHALL also return evaluations with activa=False
- Results SHALL include soft-deleted evaluations (with_deleted) for audit purposes

#### Scenario: Admin convocatorias incluye inactivas
- **WHEN** calling GET /api/coloquios/admin/convocatorias?incluir_inactivas=true
- **THEN** both active and inactive evaluations SHALL be returned

#### Scenario: Admin convocatorias solo activas por defecto
- **WHEN** calling GET /api/coloquios/admin/convocatorias without incluir_inactivas
- **THEN** only active evaluations SHALL be returned

