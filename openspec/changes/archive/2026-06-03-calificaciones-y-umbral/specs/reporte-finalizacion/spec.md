## ADDED Requirements

### Requirement: Import completion report (F1.2, RN-07, RN-08)

The system SHALL accept a completion report file exported from the LMS that indicates which activities each student has submitted. The system SHALL cross-reference this report with existing Calificacion records to detect activities that are "finalizadas por el alumno pero sin calificación registrada" — i.e., possible uncorrected submissions.

**Processing rules:**
- Only textual-scale activities SHALL be analyzed (RN-08: "únicamente actividades de escala textual")
- Numeric activity columns SHALL be skipped (absence of numeric grade = not submitted, not pending review)
- An activity is "posible sin corregir" if:
  1. The completion status indicates the student submitted/finalized the activity (e.g., "Entregado", "Finalizado", "Completado")
  2. There is NO existing Calificacion record for that (entrada_padron_id, actividad) combination
- Identifying columns (nombre, apellidos, email) SHALL be used to match students to existing EntradaPadron records

#### Scenario: Report detects textual activities pending review
- **GIVEN** a completion report file with columns: `nombre`, `apellidos`, `TP Escrito`, `Participacion`, `TP1 (Real)`
- **AND** `TP Escrito` has textual completion values, `Participacion` has textual values, `TP1 (Real)` is a numeric activity
- **WHEN** calling reporte_finalizacion(file_content, filename, materia_id, cohorte_id)
- **THEN** only `TP Escrito` and `Participacion` SHALL be analyzed (textual only, per RN-08)
- **AND** `TP1 (Real)` SHALL be skipped because it is numeric

#### Scenario: Report detects student with submitted activity but no grade
- **GIVEN** a completion report where Student A has "Entregado" for activity "TP Escrito"
- **AND** NO Calificacion record exists for Student A + "TP Escrito"
- **WHEN** calling reporte_finalizacion()
- **THEN** "TP Escrito" SHALL appear in the response's posibles_sin_corregir list
- **AND** Student A SHALL be listed under that activity

#### Scenario: Report excludes activities that already have grades
- **GIVEN** a completion report where Student B has "Entregado" for "TP Escrito"
- **AND** a Calificacion record EXISTS for Student B + "TP Escrito" with aprobado=true
- **WHEN** calling reporte_finalizacion()
- **THEN** Student B SHALL NOT appear in posibles_sin_corregir for "TP Escrito"

#### Scenario: Report excludes non-submitted activities
- **GIVEN** a completion report where Student C has "No entregado" for "TP Escrito"
- **WHEN** calling reporte_finalizacion()
- **THEN** Student C SHALL NOT appear in posibles_sin_corregir for "TP Escrito"

#### Scenario: Report returns grouped by activity
- **GIVEN** a completion report with multiple students having submitted activities without grades across 2 textual activities
- **WHEN** calling reporte_finalizacion()
- **THEN** the response SHALL contain a list of ReporteActividadSinCorregir, one per activity with pending reviews
- **AND** each entry SHALL list the affected students (nombre, apellidos, email)

#### Scenario: Report with no pending reviews returns empty list
- **GIVEN** a completion report where all submitted activities already have Calificacion records
- **WHEN** calling reporte_finalizacion()
- **THEN** the response SHALL have an empty posibles_sin_corregir list

#### Scenario: Report returns total activities reviewed count
- **GIVEN** a completion report with 5 textual activity columns
- **WHEN** calling reporte_finalizacion()
- **THEN** total_actividades_revisadas SHALL be 5

#### Scenario: Report handles students not in padrón gracefully
- **GIVEN** a completion report with a student whose nombre/apellidos do NOT match any EntradaPadron for the materia
- **WHEN** calling reporte_finalizacion()
- **THEN** the unmatched student SHALL be collected in an errors/warnings list
- **AND** processing SHALL continue for other students
