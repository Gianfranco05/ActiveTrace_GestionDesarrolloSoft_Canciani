## ADDED Requirements

### Requirement: GET /api/equipos/mis-equipos — mis equipos del docente autenticado (F4.2)

The system SHALL provide an endpoint for authenticated users to view their own active Asignaciones across all academic contexts.

- Method: GET
- Path: `/api/equipos/mis-equipos`
- Guard: `require_authenticated` (any authenticated role: PROFESOR, TUTOR, NEXO, COORDINADOR)
- Query params: `estado` (str?, "Vigente" | "Vencida" | "Futuro" — default "Vigente"), `materia_id` (UUID?, filter), `rol_id` (UUID?, filter), `carrera_id` (UUID?, filter), `cohorte_id` (UUID?, filter), `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[AsignacionResponse], "total": int, "offset": int, "limit": int}`
- The usuario SHALL be resolved from the authenticated session (JWT), never from a parameter
- Each item SHALL include the derived `estado_vigencia` field
- The endpoint SHALL respect tenant isolation — only assignments from the user's tenant

#### Scenario: Mis equipos returns own active assignments
- **WHEN** an authenticated user with active Asignaciones calls GET /api/equipos/mis-equipos
- **THEN** a paginated response SHALL be returned with AsignacionResponse items for that user only
- **AND** the items SHALL be filtered by the authenticated user's identity

#### Scenario: Mis equipos filters by estado
- **WHEN** calling GET /api/equipos/mis-equipos?estado=Vencida
- **THEN** only expired Asignaciones for the authenticated user SHALL be returned

#### Scenario: Mis equipos can return all estados
- **WHEN** calling GET /api/equipos/mis-equipos?estado=Todos
- **THEN** all Asignaciones for the authenticated user SHALL be returned regardless of estado_vigencia

#### Scenario: Mis equipos returns empty for user without assignments
- **WHEN** an authenticated user with NO Asignaciones calls GET /api/equipos/mis-equipos
- **THEN** an empty list SHALL be returned

#### Scenario: Mis equipos respects tenant isolation
- **WHEN** two users from different tenants have identical data
- **THEN** each SHALL only see their own tenant's Asignaciones

### Requirement: GET /api/equipos — listar equipos del tenant (F4.3)

The system SHALL provide an endpoint for COORDINADOR/ADMIN to list all distinct teams in the tenant, grouped by (materia_id, carrera_id, cohorte_id).

- Method: GET
- Path: `/api/equipos`
- Guard: `require_permission("equipos:asignar")`
- Query params: `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[EquipoResponse], "total": int, "offset": int, "limit": int}`
- Each EquipoResponse SHALL include materia_id, carrera_id, cohorte_id, materia_nombre, carrera_nombre, cohorte_nombre, total_asignaciones

#### Scenario: List equipos returns grouped teams
- **WHEN** calling GET /api/equipos with a valid token having equipos:asignar
- **THEN** a paginated response SHALL be returned with distinct (materia, carrera, cohorte) groups and counts

#### Scenario: List equipos returns 403 without permission
- **WHEN** calling GET /api/equipos without equipos:asignar permission
- **THEN** 403 Forbidden SHALL be returned

### Requirement: GET /api/equipos/detail — detalle de un equipo (F4.3)

The system SHALL provide a detail endpoint for a specific equipo identified by (materia_id, carrera_id, cohorte_id).

- Method: GET
- Path: `/api/equipos/detail`
- Guard: `require_permission("equipos:asignar")`
- Query params: `materia_id` (UUID, required), `carrera_id` (UUID, required), `cohorte_id` (UUID, required)
- Response: EquipoDetailResponse with materia_id, carrera_id, cohorte_id, asignaciones (list[AsignacionResponse])

#### Scenario: Get equipo detail returns all asignaciones
- **WHEN** calling GET /api/equipos/detail with valid materia_id, carrera_id, cohorte_id
- **THEN** an EquipoDetailResponse SHALL be returned with all Asignaciones for that equipo

#### Scenario: Get equipo detail returns 404
- **WHEN** calling GET /api/equipos/detail with a combination that has no Asignaciones
- **THEN** 404 Not Found SHALL be returned

### Requirement: GET /api/equipos/usuarios/search — búsqueda de usuarios para asignación (RN-30)

The system SHALL provide an autocomplete search endpoint for finding Usuarios by name, apellidos, or legajo.

- Method: GET
- Path: `/api/equipos/usuarios/search`
- Guard: `require_permission("equipos:asignar")`
- Query params: `q` (str, required — search term), `limit` (int, default 20, max 50)
- Response: `{"items": list[UsuarioSearchResponse]}`
- Search SHALL use ILIKE on nombre, apellidos, legajo fields
- Results SHALL be limited to the current tenant
- Results SHALL exclude soft-deleted Usuarios

#### Scenario: Search usuarios by name returns matches
- **WHEN** calling GET /api/equipos/usuarios/search?q=Martín
- **THEN** Usuarios with "martín" in nombre or apellidos SHALL be returned

#### Scenario: Search usuarios by legajo returns match
- **WHEN** calling GET /api/equipos/usuarios/search?q=LEG-001
- **THEN** the Usuario with legajo "LEG-001" SHALL be returned

#### Scenario: Search usuarios returns empty for no matches
- **WHEN** calling GET /api/equipos/usuarios/search?q=XXXXXXXXXX
- **THEN** an empty list SHALL be returned
