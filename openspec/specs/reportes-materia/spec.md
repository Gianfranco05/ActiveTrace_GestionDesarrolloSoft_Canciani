# reportes-materia Specification

## Purpose
TBD - created by archiving change analisis-atrasados-reportes. Update Purpose after archive.
## Requirements
### Requirement: Quick report per materia
The system SHALL provide aggregated academic metrics for a given materia, including total enrolled students, students with grades, approved count, at-risk count, and activity distribution.

#### Scenario: Report returns correct aggregates
- **WHEN** materia X has 30 enrolled students, 25 have grades, 18 have at least one approved activity, 7 are flagged as atrasados
- **THEN** the report SHALL return: total_alumnos=30, alumnos_con_nota=25, alumnos_aprobados=18, alumnos_atrasados=7, pct_aprobados=60.0%, pct_atrasados=23.3%

#### Scenario: Report response format
- **WHEN** the system returns report for materia {id}
- **THEN** the response SHALL include: materia_id, materia_nombre, cohorte_id, cohorte_nombre, total_alumnos, alumnos_con_nota, alumnos_aprobados, alumnos_atrasados, pct_aprobados, pct_atrasados, actividades_count, ultima_importacion

#### Scenario: Report for materia without data
- **WHEN** a materia has an active padron but no Calificacion records
- **THEN** the report SHALL return `total_alumnos` from padron, `alumnos_con_nota=0`, `alumnos_atrasados=total_alumnos`
- **AND** the response SHALL include a `sin_datos: true` flag

#### Scenario: Report via path parameter
- **WHEN** the client calls GET /api/analisis/reportes/materia/{materia_id}
- **THEN** the system SHALL return the report for that materia across its active cohortes

### Requirement: Export TPs sin corregir to CSV
The system SHALL export a CSV file listing students who submitted textual-scale activities that have not been graded yet (RN-07, RN-08). Only activities of type `Textual` SHALL be included — numeric activities without a grade mean the student did NOT submit (RN-08).

#### Scenario: CSV lists textual activities without grade
- **WHEN** materia X has 5 Textual-type calificaciones without nota_numerica AND nota_textual (both null) across 3 students
- **THEN** the CSV SHALL contain 5 rows: one per pending activity × student combination

#### Scenario: Numeric activities without grade are excluded
- **WHEN** a Calificacion record has `tipo='Numerica'` and `nota_numerica IS NULL`
- **THEN** that record SHALL NOT appear in the CSV export

#### Scenario: Only pending (null grade) textual activities
- **WHEN** a textual Calificacion has a non-null nota_numerica OR nota_textual
- **THEN** that record SHALL NOT appear in the CSV export (already graded)

#### Scenario: CSV response format
- **WHEN** the client calls GET /api/analisis/export/tps-sin-corregir?materia_id=X&cohorte_id=Y
- **THEN** the response SHALL be a CSV file with Content-Type: text/csv
- **AND** columns SHALL be: actividad, alumno_nombre, alumno_apellidos, alumno_email, comision
- **AND** the filename SHALL include materia ID and timestamp

#### Scenario: Empty CSV
- **WHEN** there are no pending textual activities for the given materia×cohorte
- **THEN** the response SHALL return an empty CSV with only headers

