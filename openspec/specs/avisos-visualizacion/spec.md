# avisos-visualizacion Specification

## Purpose
Visualización de avisos por destinatario según rol, alcance, cohorte y ventana de vigencia (RN-18, RN-20). Define cómo un usuario autenticado consulta los avisos que le corresponden según su perfil y contexto académico.

## ADDED Requirements

### Requirement: Listar avisos visibles para el usuario autenticado (F3.5, RN-18, RN-20, FL-09 paso 3-5)
The system SHALL return avisos filtered by the authenticated user's role, assigned materias and cohortes, within the active visibility window (`inicio_en` ≤ now ≤ `fin_en`), with `activo=true`, and not soft-deleted. Avisos with `requiere_ack=true` that the user has already acknowledged SHALL be excluded.

- Method: GET
- Path: `/api/avisos`
- Guard: `require_authenticated` (any authenticated user)
- Query params: `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response 200: `{"items": list[AvisoListItemResponse], "total": int, "offset": int, "limit": int}`
- Each `AvisoListItemResponse` SHALL include: `id`, `alcance`, `severidad`, `titulo`, `inicio_en`, `fin_en`, `orden`, `requiere_ack`, `acknowledged` (bool — whether the current user has confirmed), `created_at`
- The system SHALL apply the following visibility filters:
  1. `deleted_at IS NULL`
  2. `activo = true`
  3. `inicio_en <= NOW() AND fin_en >= NOW()` (RN-18)
  4. Audience matching (RN-20):
     - If `alcance = Global`: visible to ALL authenticated users
     - If `alcance = PorMateria`: visible ONLY if the user has an active Asignacion with that `materia_id`
     - If `alcance = PorCohorte`: visible ONLY if the user has an active Asignacion with that `cohorte_id`
     - If `alcance = PorRol`: visible ONLY if the user has an active Asignacion with a role matching `rol_destino`
  5. If `requiere_ack = true`, exclude avisos where the user has an existing `AcknowledgmentAviso` record
- Results SHALL be ordered by `orden` DESC, then `inicio_en` DESC (higher priority and newer avisos first)
- The system SHALL scope all queries to the user's `tenant_id`

#### Scenario: PROFESOR ve avisos globales y de sus materias
- **WHEN** a PROFESOR with Asignaciones to Materia-X and Cohorte-Y calls GET /api/avisos
- **THEN** the system SHALL return avisos with `alcance=Global`
- **AND** avisos with `alcance=PorMateria` and `materia_id=Materia-X`
- **AND** avisos with `alcance=PorCohorte` and `cohorte_id=Cohorte-Y`
- **AND** avisos with `alcance=PorRol` and `rol_destino=PROFESOR`
- **AND** NOT avisos with `alcance=PorMateria` and `materia_id=Materia-Z` (not assigned)

#### Scenario: COORDINADOR ve todos los avisos por tener múltiples roles
- **WHEN** a COORDINADOR calls GET /api/avisos
- **THEN** the system SHALL return all avisos matching any of the COORDINADOR's active Asignaciones across all materias and cohortes

#### Scenario: ALUMNO solo ve avisos de su cohorte y globales
- **WHEN** an ALUMNO assigned to Cohorte-Y calls GET /api/avisos
- **THEN** the system SHALL return avisos with `alcance=Global`
- **AND** avisos with `alcance=PorCohorte` and `cohorte_id=Cohorte-Y`
- **AND** avisos with `alcance=PorRol` and `rol_destino=ALUMNO`
- **AND** NOT avisos with `alcance=PorMateria` (ALUMNO does not have Asignacion records with materia)

#### Scenario: Aviso fuera de ventana de vigencia no se muestra (RN-18)
- **WHEN** an aviso has `inicio_en: 2026-07-01`, `fin_en: 2026-07-31`, and the current date is 2026-06-03
- **THEN** the aviso SHALL NOT appear in GET /api/avisos
- **AND** when the same aviso had `inicio_en: 2026-01-01`, `fin_en: 2026-01-31` (already expired)
- **THEN** it SHALL NOT appear in GET /api/avisos either

#### Scenario: Aviso con requiere_ack ya confirmado no se muestra
- **WHEN** an aviso has `requiere_ack=true` and the user has an `AcknowledgmentAviso` record for it
- **THEN** the aviso SHALL NOT appear in GET /api/avisos for that user

#### Scenario: Aviso con requiere_ack sin confirmar sí se muestra
- **WHEN** an aviso has `requiere_ack=true` and the user has NO `AcknowledgmentAviso` record for it
- **THEN** the aviso SHALL appear in GET /api/avisos for that user

#### Scenario: Aviso inactivo no se muestra
- **WHEN** an aviso has `activo=false`
- **THEN** the aviso SHALL NOT appear in GET /api/avisos even if within the vigencia window

#### Scenario: Aviso soft-deleted no se muestra
- **WHEN** an aviso has `deleted_at IS NOT NULL`
- **THEN** the aviso SHALL NOT appear in GET /api/avisos

#### Scenario: Ordenamiento por prioridad y fecha
- **WHEN** there are 3 avisos: A (orden=10, inicio_en=2026-06-01), B (orden=5, inicio_en=2026-06-03), C (orden=10, inicio_en=2026-05-01)
- **THEN** the results SHALL be ordered: A (orden=10, más reciente), then C (orden=10, más antiguo), then B (orden=5)

#### Scenario: Listado sin autenticación
- **WHEN** an unauthenticated request sends GET /api/avisos
- **THEN** the system SHALL respond 401 Unauthorized

#### Scenario: Paginación respeta límites
- **WHEN** calling GET /api/avisos?offset=0&limit=10 and there are 25 visible avisos
- **THEN** the system SHALL return items with 10 avisos and total=25

#### Scenario: Profesor sin asignaciones obtiene lista vacía
- **WHEN** a PROFESOR with NO active Asignaciones calls GET /api/avisos
- **THEN** the system SHALL return avisos with `alcance=Global` only
- **AND** NOT return avisos with `alcance=PorMateria`, `alcance=PorCohorte`, or `alcance=PorRol`
