## ADDED Requirements

### Requirement: Detect at-risk students per materia×cohorte
The system SHALL detect which students are "atrasados" for a given materia and cohorte combination, based on RN-06. A student is atrasado if they have missing activities OR their grade is below the configured umbral for any activity. Cross-references Calificacion (existing grades) with EntradaPadron (enrolled students) and UmbralMateria (threshold configuration).

#### Scenario: Student with missing activity is flagged as atrasado
- **WHEN** a materia has 5 activities and a student has Calificacion records for only 3 of them
- **THEN** the system SHALL include that student in the atrasados list with motivo "actividades_faltantes"

#### Scenario: Student with grade below umbral is flagged as atrasado
- **WHEN** a student has a Calificacion record with `aprobado=False` for an activity
- **THEN** the system SHALL include that student in the atrasados list with motivo "nota_baja"

#### Scenario: Student meets both conditions
- **WHEN** a student has missing activities AND grade below umbral
- **THEN** the system SHALL include the student once with motivo "ambos" and both activity lists populated

#### Scenario: Student with all activities approved is NOT atrasado
- **WHEN** a student has Calificacion records for all activities and all have `aprobado=True`
- **THEN** the system SHALL NOT include that student in the atrasados list

#### Scenario: No Calificacion records exist yet
- **WHEN** a materia has an active VersionPadron with enrolled students but no grades have been imported yet
- **THEN** the system SHALL mark ALL enrolled students as atrasados with motivo "actividades_faltantes"
- **AND** the response SHALL include a `sin_datos` flag indicating no grade data exists

#### Scenario: Atrasados response format
- **WHEN** the system returns atrasados for `(materia_id, cohorte_id)`
- **THEN** each atrasado entry SHALL include: entrada_padron_id, nombre, apellidos, email, comision, motivo, actividades_faltantes list, actividades_reprobadas list

#### Scenario: Scope isolation — PROFESOR sees only their materias
- **WHEN** a PROFESOR queries atrasados
- **THEN** the results SHALL be scoped to materias where the user has an active asignacion
- **AND** COORDINADOR/ADMIN SHALL see all materias in the tenant

#### Scenario: Unauthorized access returns 403
- **WHEN** a user without the `atrasados:ver` permission calls GET /api/analisis/atrasados
- **THEN** the system SHALL return 403 Forbidden

### Requirement: Filter atrasados by materia and cohorte
The system SHALL accept optional `materia_id` and `cohorte_id` query parameters to filter the atrasados list. If omitted, return data for all materias and cohorts accessible to the user within their scope.

#### Scenario: Filter by materia_id
- **WHEN** the client passes `?materia_id=<uuid>` 
- **THEN** the system SHALL return atrasados only for that materia

#### Scenario: Filter by materia_id and cohorte_id
- **WHEN** the client passes `?materia_id=<uuid>&cohorte_id=<uuid>`
- **THEN** the system SHALL return atrasados only for that materia and cohorte combination

#### Scenario: No filters — all accessible materias
- **WHEN** the client calls GET /api/analisis/atrasados without filters
- **THEN** the system SHALL return atrasados grouped by materia across all materias the user can access
