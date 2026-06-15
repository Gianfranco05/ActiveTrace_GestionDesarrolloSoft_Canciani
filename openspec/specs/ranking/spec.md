# ranking Specification

## Purpose
TBD - created by archiving change analisis-atrasados-reportes. Update Purpose after archive.
## Requirements
### Requirement: Rank students by approved activity count
The system SHALL compute a ranking of students sorted by the number of approved activities, for a given materia and cohorte. Only students with at least one approved activity SHALL be included (RN-09). The ranking SHALL be ordered descending by approval count.

#### Scenario: Ranking returns students with ≥1 approved activity
- **WHEN** materia X has 5 students: A (4 approved), B (2 approved), C (1 approved), D (0 approved), E (no Calificacion records)
- **THEN** the ranking SHALL include A, B, C in that order
- **AND** D and E SHALL be excluded from the ranking

#### Scenario: Ties are ordered alphabetically
- **WHEN** two students have the same number of approved activities
- **THEN** they SHALL be ordered alphabetically by apellidos, then nombre

#### Scenario: Ranking response format
- **WHEN** the system returns ranking for `(materia_id, cohorte_id)`
- **THEN** each row SHALL include: posicion, entrada_padron_id, nombre, apellidos, aprobadas (count), total_actividades, porcentaje (aprobadas/total * 100)

#### Scenario: Empty ranking
- **WHEN** no student has any approved activity
- **THEN** the system SHALL return an empty list
- **AND** the response SHALL include a `total_aprobados: 0` field

#### Scenario: Scope isolation on ranking
- **WHEN** a PROFESOR queries ranking
- **THEN** results SHALL be scoped to materias where the user has asignacion

### Requirement: Compute final grades per student
The system SHALL compute a final grade for each student by aggregating all their numeric Calificacion records. The aggregation SHALL use the average of all numeric `nota_numerica` values. Textual-only activities SHALL be excluded from the numeric average. A status label SHALL be derived based on the ratio of approved activities to total activities.

#### Scenario: Final grade is average of numeric calificaciones
- **WHEN** a student has numeric grades 80, 90, and 70 for 3 different activities
- **THEN** the nota_promedio SHALL be 80.0 (average)

#### Scenario: Student with textual-only activities
- **WHEN** a student has Calificacion records with `tipo='Textual'` and no numeric grades
- **THEN** the nota_promedio SHALL be null
- **AND** the response SHALL indicate "Sin nota numérica"

#### Scenario: Final grade state derivation
- **WHEN** a student has >= 60% of activities approved
- **THEN** the estado SHALL be "Regular"
- **WHEN** a student has < 60% of activities approved
- **THEN** the estado SHALL be "Libre"
- **WHEN** a student has no Calificacion records
- **THEN** the estado SHALL be "Sin datos"

#### Scenario: Notas finales response format
- **WHEN** the system returns notas-finales for `(materia_id, cohorte_id)`
- **THEN** each row SHALL include: entrada_padron_id, nombre, apellidos, nota_promedio, actividades_aprobadas, total_actividades, estado

