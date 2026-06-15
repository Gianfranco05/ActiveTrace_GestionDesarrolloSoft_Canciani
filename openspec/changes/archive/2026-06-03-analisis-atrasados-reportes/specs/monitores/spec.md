## ADDED Requirements

### Requirement: Monitor general view (COORDINADOR/ADMIN)
The system SHALL provide a cross-materia aggregate view showing academic status across all materias accessible to COORDINADOR and ADMIN roles. Each row SHALL represent one materia with aggregate metrics.

#### Scenario: General monitor returns all materias
- **WHEN** a COORDINADOR or ADMIN calls GET /api/analisis/monitor/general
- **THEN** the system SHALL return one row per materia across the entire tenant

#### Scenario: General monitor row format
- **WHEN** the system returns the general monitor
- **THEN** each row SHALL include: materia_id, materia_nombre, cohorte_id, cohorte_nombre, total_alumnos, aprobados, atrasados, pct_aprobacion

#### Scenario: General monitor access denied for PROFESOR/TUTOR
- **WHEN** a PROFESOR or TUTOR calls GET /api/analisis/monitor/general
- **THEN** the system SHALL return 403 Forbidden

### Requirement: Monitor seguimiento (PROFESOR/TUTOR)
The system SHALL provide a per-materia detailed view for PROFESOR and TUTOR roles, scoped to their assigned materias. Shows each student's individual status within a materia.

#### Scenario: Seguimiento shows scoped materias
- **WHEN** a PROFESOR with 3 assigned materias calls GET /api/analisis/monitor/seguimiento
- **THEN** the system SHALL only return data for those 3 materias

#### Scenario: Seguimiento filtered by materia
- **WHEN** the client passes `?materia_id=<uuid>`
- **THEN** the system SHALL return seguimiento data only for that materia

#### Scenario: Seguimiento row format
- **WHEN** the system returns seguimiento for a materia
- **THEN** each row SHALL include: entrada_padron_id, nombre, apellidos, email, comision, actividades_aprobadas, actividades_reprobadas, actividades_faltantes, nota_promedio, estado ("Al día" | "Atrasado" | "Sin datos")

#### Scenario: Seguimiento student status derivation
- **WHEN** a student has >= 60% of activities approved
- **THEN** the estado SHALL be "Al día"
- **WHEN** a student has < 60% approved OR missing activities
- **THEN** the estado SHALL be "Atrasado"
- **WHEN** a student has no Calificacion records
- **THEN** the estado SHALL be "Sin datos"

### Requirement: Monitor coordinación (COORDINADOR/ADMIN)
The system SHALL provide a full cross-materia view with optional date range filter. Extends the general monitor (F2.9) by filtering Calificacion records by `importado_at` range.

#### Scenario: Coordinación without date filters
- **WHEN** a COORDINADOR calls GET /api/analisis/monitor/coordinacion without filters
- **THEN** the system SHALL return all materias (same as general monitor)

#### Scenario: Coordinación with date range
- **WHEN** the client passes `?desde=2026-03-01&hasta=2026-03-31`
- **THEN** the system SHALL only count Calificacion records where `importado_at` falls within that range
- **AND** metrics SHALL reflect only that period

#### Scenario: Coordinación filtered by materia
- **WHEN** the client passes `?materia_id=<uuid>&desde=2026-03-01&hasta=2026-03-31`
- **THEN** the system SHALL return data for that materia within the date range

#### Scenario: Coordinación row format
- **WHEN** the system returns coordinación data
- **THEN** each row SHALL include: materia_id, materia_nombre, cohorte_id, cohorte_nombre, total_alumnos, aprobados, atrasados, pct_aprobacion, period_desde, period_hasta
