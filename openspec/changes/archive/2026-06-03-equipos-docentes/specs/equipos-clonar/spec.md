## ADDED Requirements

### Requirement: POST /api/equipos/clonar — clonar equipo entre períodos (F4.5, RN-12)

The system SHALL provide an endpoint to duplicate all active Asignaciones from a source equipo (materia × carrera × cohorte) to a destination equipo with new vigencia dates.

- Method: POST
- Path: `/api/equipos/clonar`
- Guard: `require_permission("equipos:asignar")`
- Request body: ClonarRequest
  - `origen_materia_id` (UUID, required)
  - `origen_carrera_id` (UUID, required)
  - `origen_cohorte_id` (UUID, required)
  - `destino_materia_id` (UUID, required)
  - `destino_carrera_id` (UUID, required)
  - `destino_cohorte_id` (UUID, required)
  - `nueva_vig_desde` (date, required)
  - `nueva_vig_hasta` (date?, optional)
  - `model_config = ConfigDict(extra='forbid')`
- Response: 201 Created with EquipoDetailResponse of the destination equipo
- The operation SHALL be transactional — all assignments cloned or NONE
- Only assignments with deleted_at IS NULL AND estado_vigencia = "Vigente" SHALL be cloned
- Cloned assignments SHALL have:
  - Same usuario_id, rol_id, comisiones from origin
  - destino_materia_id, destino_carrera_id, destino_cohorte_id as provided
  - nueva_vig_desde, nueva_vig_hasta as provided
  - responsable_id resolved: if the original responsable_id points to another Asignacion in the origin team AND that usuario was also cloned to the destination, the new responsable_id SHALL point to the corresponding new Asignacion in the destination
  - If responsable resolution fails (original responsable not in destination), responsable_id SHALL be None
- The endpoint SHALL return 404 if the origin equipo has no active Asignaciones
- The endpoint SHALL generate audit `ASIGNACION_MODIFICAR` with filas_afectadas = number of cloned assignments

#### Scenario: Clonar equipo duplicates active assignments
- **WHEN** calling POST /api/equipos/clonar with valid origen and destino parameters
- **THEN** 201 Created SHALL be returned
- **AND** the destination equipo SHALL have the same number of active Asignaciones as the origin

#### Scenario: Clonar equipo copies all assignment fields
- **WHEN** calling POST /api/equipos/clonar
- **THEN** each cloned Asignacion SHALL have the same usuario_id, rol_id, comisiones as the origin
- **AND** materia_id, carrera_id, cohorte_id SHALL be the destination values
- **AND** vig_desde, vig_hasta SHALL be the new values provided

#### Scenario: Clonar equipo resolves responsable_id
- **WHEN** cloning an equipo where the responsable is also in the equipo
- **THEN** the cloned Asignacion's responsable_id SHALL point to the corresponding new Asignacion in the destination
- **WHEN** cloning an equipo where the responsable is NOT in the equipo
- **THEN** the cloned Asignacion's responsable_id SHALL be None

#### Scenario: Clonar equipo only clones vigente assignments
- **WHEN** the origin has both Vigente and Vencida Asignaciones
- **THEN** only Vigente Asignaciones SHALL be cloned

#### Scenario: Clonar equipo returns 404 if source empty
- **WHEN** calling POST /api/equipos/clonar with an origen that has no active Asignaciones
- **THEN** 404 Not Found SHALL be returned

#### Scenario: Clonar equipo rolls back on unique violation
- **WHEN** cloning to a destino that already has conflicting Asignaciones
- **THEN** 409 Conflict SHALL be returned
- **AND** no assignments SHALL be created (full rollback)

#### Scenario: Clonar equipo generates audit
- **WHEN** calling POST /api/equipos/clonar successfully
- **THEN** an AuditLog entry with action "ASIGNACION_MODIFICAR" SHALL be created
- **AND** filas_afectadas SHALL equal the number of cloned Asignaciones
