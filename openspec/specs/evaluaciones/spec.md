# evaluaciones Specification

## Purpose
TBD - created by archiving change evaluaciones-y-coloquios. Update Purpose after archive.
## Requirements
### Requirement: POST /api/coloquios — crear convocatoria de evaluación (F7.3)

The system SHALL provide an endpoint for COORDINADOR/ADMIN to create a new evaluation instance (coloquio, parcial, TP, recuperatorio) with associated days and capacities.

- Method: POST
- Path: `/api/coloquios`
- Guard: `require_permission("coloquios:gestionar")`
- Request body: EvaluacionCreateRequest
  - `materia_id` (UUID, required)
  - `cohorte_id` (UUID, required)
  - `tipo` (Literal["Parcial", "TP", "Coloquio", "Recuperatorio"], required)
  - `instancia` (str, required, min 1, max 200)
  - `cupos_por_dia` (list[CupoPorDia], required, min 1 item)
  - `model_config = ConfigDict(extra='forbid')`
- Response: 201 Created with EvaluacionResponse
- The endpoint SHALL validate that materia_id and cohorte_id exist in the tenant
- The endpoint SHALL validate that cupos_por_dia contains no duplicate dates
- The endpoint SHALL initialize `alumnos_convocados` as empty list
- The endpoint SHALL set `activa = True` by default
- The endpoint SHALL generate audit `COLOQUIO_CREAR`

#### Scenario: Crear convocatoria exitosa
- **WHEN** calling POST /api/coloquios with valid materia_id, cohorte_id, tipo, instancia and cupos_por_dia
- **THEN** 201 Created SHALL be returned
- **AND** the response SHALL include the created Evaluacion with activa=True and alumnos_convocados=[]

#### Scenario: Crear convocatoria rechaza materia inexistente
- **WHEN** calling POST /api/coloquios with a non-existent materia_id
- **THEN** 404 Not Found SHALL be returned

#### Scenario: Crear convocatoria rechaza días duplicados
- **WHEN** calling POST /api/coloquios with cupos_por_dia containing the same date twice
- **THEN** 422 Validation Error SHALL be returned

#### Scenario: Crear convocatoria requiere al menos un día
- **WHEN** calling POST /api/coloquios with empty cupos_por_dia
- **THEN** 422 Validation Error SHALL be returned

#### Scenario: Crear convocatoria genera auditoría
- **WHEN** calling POST /api/coloquios successfully
- **THEN** an AuditLog entry with action "COLOQUIO_CREAR" SHALL be created

### Requirement: PUT /api/coloquios/{id} — actualizar convocatoria (F7.3)

The system SHALL allow COORDINADOR/ADMIN to update an existing evaluation's instancia, cupos, or active status.

- Method: PUT
- Path: `/api/coloquios/{id}`
- Guard: `require_permission("coloquios:gestionar")`
- Request body: EvaluacionUpdateRequest
  - `instancia` (str?, optional, min 1, max 200)
  - `cupos_por_dia` (list[CupoPorDia]?, optional, min 1 item)
  - `activa` (bool?, optional)
  - `model_config = ConfigDict(extra='forbid')`
- Response: EvaluacionResponse with updated fields
- The endpoint SHALL generate audit `COLOQUIO_CREAR` with detalle indicating update operation

#### Scenario: Actualizar instancia
- **WHEN** calling PUT /api/coloquios/{id} with a new instancia value
- **THEN** the evaluacion's instancia SHALL be updated

#### Scenario: Actualizar convocatoria inexistente
- **WHEN** calling PUT /api/coloquios/{id} with a non-existent id
- **THEN** 404 Not Found SHALL be returned

### Requirement: GET /api/coloquios — listar convocatorias (F7.4)

The system SHALL provide a paginated list of all evaluations in the tenant with per-evaluation metrics.

- Method: GET
- Path: `/api/coloquios`
- Guard: `require_permission("coloquios:gestionar")`
- Query params: `materia_id` (UUID?, filter), `cohorte_id` (UUID?, filter), `tipo` (str?, filter), `activa` (bool?, filter), `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[EvaluacionResponse], "total": int, "offset": int, "limit": int}`
- Each item SHALL include total_convocados, total_reservas, total_resultados, cupos_libres
- Results SHALL be ordered by created_at descending

#### Scenario: Listar todas las convocatorias
- **WHEN** calling GET /api/coloquios with valid token having coloquios:gestionar
- **THEN** a paginated list of EvaluacionResponse items SHALL be returned

#### Scenario: Filtrar por materia
- **WHEN** calling GET /api/coloquios?materia_id=<uuid>
- **THEN** only evaluations for that materia SHALL be returned

#### Scenario: Filtrar solo activas
- **WHEN** calling GET /api/coloquios?activa=true
- **THEN** only evaluations with activa=True SHALL be returned

#### Scenario: Listar retorna 403 sin permiso
- **WHEN** calling GET /api/coloquios without coloquios:gestionar permission
- **THEN** 403 Forbidden SHALL be returned

### Requirement: GET /api/coloquios/{id} — detalle de convocatoria (F7.4)

The system SHALL provide detailed view of a single evaluation including the list of convoked students.

- Method: GET
- Path: `/api/coloquios/{id}`
- Guard: `require_permission("coloquios:gestionar")`
- Response: EvaluacionDetailResponse with alumnos_convocados list

#### Scenario: Obtener detalle con alumnos convocados
- **WHEN** calling GET /api/coloquios/{id} with a valid id
- **THEN** the full detail SHALL be returned including the alumnos_convocados array

#### Scenario: Obtener detalle inexistente
- **WHEN** calling GET /api/coloquios/{id} with a non-existent id
- **THEN** 404 Not Found SHALL be returned

### Requirement: PUT /api/coloquios/{id}/convocados — importar alumnos a convocatoria (F7.2)

The system SHALL allow COORDINADOR/ADMIN to import eligible students into an evaluation, either manually or from the academic padrón.

- Method: PUT
- Path: `/api/coloquios/{id}/convocados`
- Guard: `require_permission("coloquios:gestionar")`
- Request body: ImportarAlumnosRequest
  - `modo` (Literal["manual", "padron"], required)
  - `usuario_ids` (list[UUID]?, optional, max 500 — modo manual)
  - `materia_id` (UUID?, optional — modo padrón)
  - `cohorte_id` (UUID?, optional — modo padrón)
  - `model_config = ConfigDict(extra='forbid')`
- Response: EvaluacionDetailResponse with updated alumnos_convocados
- Modo manual: replaces alumnos_convocados with the provided usuario_ids. Validates all IDs exist and have ALUMNO role.
- Modo padrón: queries EntradaPadron for the tenant filtered by materia_id and cohorte_id, extracts unique usuario_ids, sets as alumnos_convocados. Returns 400 if no padrón found.
- The endpoint SHALL validate the evaluation exists and is active
- The endpoint SHALL generate audit `COLOQUIO_CREAR` with detalle indicating import operation and count

#### Scenario: Importar alumnos manualmente
- **WHEN** calling PUT /api/coloquios/{id}/convocados with modo="manual" and 3 valid usuario_ids
- **THEN** the evaluacion's alumnos_convocados SHALL contain exactly those 3 UUIDs

#### Scenario: Importar alumnos desde padrón
- **WHEN** calling PUT /api/coloquios/{id}/convocados with modo="padron", valid materia_id and cohorte_id
- **THEN** the evaluacion's alumnos_convocados SHALL contain all alumnos from the matching padrón entries

#### Scenario: Importar alumnos rechaza usuario inexistente
- **WHEN** calling PUT /api/coloquios/{id}/convocados with modo="manual" and a non-existent usuario_id
- **THEN** 404 Not Found SHALL be returned

#### Scenario: Importar desde padrón sin datos
- **WHEN** calling PUT /api/coloquios/{id}/convocados with modo="padron" and no padrón exists for that materia/cohorte
- **THEN** 400 Bad Request SHALL be returned

#### Scenario: Importar rechaza evaluación inactiva
- **WHEN** calling PUT /api/coloquios/{id}/convocados on an evaluation with activa=False
- **THEN** 400 Bad Request SHALL be returned

### Requirement: GET /api/coloquios/metricas — panel de métricas de coloquios (F7.1)

The system SHALL provide aggregated metrics for all evaluations in the tenant.

- Method: GET
- Path: `/api/coloquios/metricas`
- Guard: `require_permission("coloquios:gestionar")`
- Response: PanelMetricasResponse
  - `total_convocatorias_activas` (int)
  - `total_convocados` (int)
  - `total_reservas_activas` (int)
  - `total_resultados` (int)
  - `tasa_aprobacion` (float?, null if no resultados)

#### Scenario: Panel con datos
- **WHEN** calling GET /api/coloquios/metricas with existing evaluations and reservations
- **THEN** all metric counts SHALL be returned with accurate values

#### Scenario: Panel vacío sin convocatorias
- **WHEN** calling GET /api/coloquios/metricas with no evaluations in the tenant
- **THEN** all counts SHALL be 0 and tasa_aprobacion SHALL be null

### Requirement: GET /api/coloquios/{id}/metricas — métricas de una convocatoria

The system SHALL provide per-evaluation metrics including counts of convoked, reserved, and resulted students.

- Method: GET
- Path: `/api/coloquios/{id}/metricas`
- Guard: `require_permission("coloquios:gestionar")`
- Response: ConvocatoriaMetricasResponse

#### Scenario: Métricas de convocatoria con reservas
- **WHEN** calling GET /api/coloquios/{id}/metricas for an evaluation with convoked students and active reservations
- **THEN** accurate counts SHALL be returned for total_convocados, total_reservas, total_resultados, and cupos_libres

#### Scenario: Métricas de convocatoria inexistente
- **WHEN** calling GET /api/coloquios/{id}/metricas for a non-existent id
- **THEN** 404 Not Found SHALL be returned

