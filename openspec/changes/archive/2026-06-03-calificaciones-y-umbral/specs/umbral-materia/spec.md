## ADDED Requirements

### Requirement: Get umbral for materia

The system SHALL allow querying the active UmbralMateria configuration for a given materia. If no configuration exists, the system SHALL return the default values (umbral_pct=60, valores_aprobatorios=["Satisfactorio", "Supera lo esperado"]).

#### Scenario: Get umbral when configuration exists
- **GIVEN** an existing UmbralMateria with umbral_pct=75 for materia_id=X
- **WHEN** getting the umbral for materia_id=X
- **THEN** the response SHALL contain umbral_pct=75, valores_aprobatorios matching the stored values

#### Scenario: Get umbral returns defaults when no configuration exists
- **GIVEN** NO UmbralMateria for materia_id=X
- **WHEN** getting the umbral for materia_id=X
- **THEN** the response SHALL contain umbral_pct=60, valores_aprobatorios=["Satisfactorio", "Supera lo esperado"]

#### Scenario: Get umbral returns 404 for non-existent materia
- **WHEN** getting the umbral for a non-existent materia_id
- **THEN** a 404 error SHALL be returned

---

### Requirement: Set/update umbral for materia (F2.1, RN-03)

The system SHALL allow setting or updating the UmbralMateria configuration for a materia. The operation SHALL be an upsert — if a configuration already exists, it SHALL be updated; if not, a new one SHALL be created.

**Validation rules:**
- `umbral_pct` SHALL be an integer between 1 and 100 (inclusive)
- `materia_id` SHALL reference an existing materia

**Important — No retroactive effect**: Changing the umbral SHALL NOT update existing Calificacion records. The `aprobado` field on existing records is frozen at import time.

#### Scenario: Set umbral creates new configuration
- **GIVEN** NO UmbralMateria for materia_id=X
- **WHEN** setting umbral_pct=75 for materia_id=X
- **THEN** a new UmbralMateria SHALL be created with umbral_pct=75
- **AND** existing Calificacion records SHALL NOT be modified

#### Scenario: Update umbral modifies existing configuration
- **GIVEN** an existing UmbralMateria for materia_id=X with umbral_pct=50
- **WHEN** updating umbral_pct to 80 for materia_id=X
- **THEN** the UmbraMateria SHALL have umbral_pct=80
- **AND** existing Calificacion records SHALL NOT be modified

#### Scenario: Validate umbral_pct range
- **WHEN** setting umbral_pct to 0
- **THEN** a validation error SHALL be raised
- **WHEN** setting umbral_pct to 101
- **THEN** a validation error SHALL be raised

#### Scenario: Set umbral with custom valores_aprobatorios
- **WHEN** setting umbral_pct=60 with valores_aprobatorios=["Aprobado", "Promocionado", "Satisfactorio"]
- **THEN** the stored valores_aprobatorios SHALL be ["Aprobado", "Promocionado", "Satisfactorio"]

#### Scenario: Set umbral for non-existent materia
- **WHEN** setting umbral for a non-existent materia_id
- **THEN** a 404 error SHALL be raised

#### Scenario: Calificaciones with the old umbral remain unchanged after umbral update
- **GIVEN** a Calificacion with nota_numerica=50, aprobado=false (created when umbral was 60)
- **WHEN** updating the umbral to 40
- **THEN** the existing Calificacion's aprobado SHALL remain false
