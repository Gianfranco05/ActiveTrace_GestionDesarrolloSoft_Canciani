## ADDED Requirements

### Requirement: Calificacion ORM model

The system SHALL define a Calificacion ORM model representing a single grade entry for a student in an evaluable activity of a subject. The model SHALL extend BaseModelMixin (UUID PK, tenant_id FK, created_at, updated_at, deleted_at).

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK via BaseModelMixin |
| `tenant_id` | UUID | FK → Tenant via BaseModelMixin |
| `materia_id` | UUID | FK → Materia(id), NOT NULL |
| `cohorte_id` | UUID | FK → Cohorte(id), NOT NULL |
| `entrada_padron_id` | UUID | FK → EntradaPadron(id), NOT NULL |
| `actividad` | String(200) | Name of the evaluable activity, NOT NULL |
| `tipo` | String(20) | "Numerica" or "Textual", NOT NULL |
| `nota_numerica` | Numeric(5,2) | Numeric score, nullable (null if textual type) |
| `nota_textual` | Text | Textual assessment, nullable (null if numeric type) |
| `aprobado` | Boolean | DERIVED at import time, NOT NULL — see derivation rules below |
| `origen` | String(20) | "Importado" or "Manual", NOT NULL, default "Importado" |
| `cargado_por` | UUID | FK → Usuario(id), NOT NULL — who imported the grade |
| `importado_at` | DateTime | NOT NULL, default utcnow |
| `created_at` | DateTime | via BaseModelMixin |
| `updated_at` | DateTime | via BaseModelMixin |
| `deleted_at` | DateTime | nullable, via BaseModelMixin |

**IMPORTANT — aprobado is DERIVED and STORED**: The `aprobado` boolean SHALL be computed at grade creation time based on the active UmbralMateria configuration for the materia. It SHALL NOT be recomputed when the umbral changes later. This ensures historical accuracy — changing the threshold does NOT retroactively change existing grades.

**IMPORTANT — Scope isolation (RN-04)**: Each Calificacion record SHALL be scoped to the importing user (cargado_por). Multiple teachers importing grades for the same materia SHALL have independent grade sets.

**Derivation rules for `aprobado`:**
- If `tipo == "Numerica"`: compare `nota_numerica` against the `umbral_pct` of the active UmbralMateria for the materia. If no UmbralMateria exists, use 60% as default. The grade is aprobado if `nota_numerica >= umbral` (both on 0-100 scale).
- If `tipo == "Textual"`: check if `nota_textual` (case-insensitive, trimmed) is in the `valores_aprobatorios` set of the active UmbralMateria. If no UmbralMateria exists, use the default set: `["Satisfactorio", "Supera lo esperado"]`.

#### Scenario: Create numeric calificacion with aprobado=true
- **GIVEN** an existing UmbralMateria for the materia with umbral_pct=60
- **WHEN** creating a Calificacion with tipo="Numerica", nota_numerica=75
- **THEN** the Calificacion SHALL have aprobado=true

#### Scenario: Create numeric calificacion with aprobado=false
- **GIVEN** an existing UmbralMateria for the materia with umbral_pct=60
- **WHEN** creating a Calificacion with tipo="Numerica", nota_numerica=45
- **THEN** the Calificacion SHALL have aprobado=false

#### Scenario: Create textual calificacion with aprobado=true
- **GIVEN** an existing UmbralMateria for the materia with valores_aprobatorios=["Satisfactorio", "Supera lo esperado"]
- **WHEN** creating a Calificacion with tipo="Textual", nota_textual="Satisfactorio"
- **THEN** the Calificacion SHALL have aprobado=true

#### Scenario: Create textual calificacion with aprobado=false (not in approved set)
- **GIVEN** an existing UmbralMateria with valores_aprobatorios=["Satisfactorio", "Supera lo esperado"]
- **WHEN** creating a Calificacion with tipo="Textual", nota_textual="No satisfactorio"
- **THEN** the Calificacion SHALL have aprobado=false

#### Scenario: Default umbral (60%) when no UmbralMateria exists
- **GIVEN** NO UmbralMateria exists for the materia
- **WHEN** creating a Calificacion with tipo="Numerica", nota_numerica=60
- **THEN** aprobado SHALL be true (60 >= 60)

#### Scenario: Calificacion with null numeric grade defaults to not aprobado
- **WHEN** creating a Calificacion with tipo="Numerica", nota_numerica=None
- **THEN** aprobado SHALL be false

#### Scenario: Calificacion with null textual grade defaults to not aprobado
- **WHEN** creating a Calificacion with tipo="Textual", nota_textual=None
- **THEN** aprobado SHALL be false

#### Scenario: Aprobado is frozen at import time (umbral change does NOT retroactively affect)
- **GIVEN** an existing Calificacion with nota_numerica=50, aprobado=false (umbral was 60 at import time)
- **WHEN** the UmbralMateria umbral_pct is changed to 40
- **THEN** the existing Calificacion's aprobado SHALL remain false (not recomputed)

#### Scenario: Tenant isolation for calificacion
- **GIVEN** Calificacions in two different tenants
- **WHEN** querying calificacions filtered by tenant_id
- **THEN** only calificacions belonging to that tenant SHALL be returned

---

### Requirement: UmbralMateria ORM model

The system SHALL define an UmbralMateria ORM model representing the passing threshold configuration for a subject. The model SHALL extend BaseModelMixin (UUID PK, tenant_id FK, timestamps, soft delete).

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK via BaseModelMixin |
| `tenant_id` | UUID | FK → Tenant via BaseModelMixin |
| `materia_id` | UUID | FK → Materia(id), NOT NULL |
| `asignacion_id` | UUID | FK → Asignacion(id), NULLABLE (reserved for future per-teacher override) |
| `umbral_pct` | Integer | NOT NULL, default 60, validated 1–100 |
| `valores_aprobatorios` | ARRAY(String) | NOT NULL, default ["Satisfactorio", "Supera lo esperado"] |
| `created_at` | DateTime | via BaseModelMixin |
| `updated_at` | DateTime | via BaseModelMixin |
| `deleted_at` | DateTime | nullable, via BaseModelMixin |

**Unique constraint**: One active UmbralMateria per (tenant_id, materia_id, asignacion_id) WHERE deleted_at IS NULL. When asignacion_id IS NULL, there is one default threshold per materia.

#### Scenario: Create UmbralMateria with default values
- **WHEN** creating an UmbralMateria for a materia without specifying umbral_pct or valores_aprobatorios
- **THEN** umbral_pct SHALL be 60
- **AND** valores_aprobatorios SHALL be ["Satisfactorio", "Supera lo esperado"]

#### Scenario: Create UmbralMateria with custom values
- **WHEN** creating an UmbralMateria with umbral_pct=75, valores_aprobatorios=["Aprobado", "Promocionado"]
- **THEN** the stored values SHALL match the provided ones

#### Scenario: Upsert replaces existing configuration
- **GIVEN** an existing UmbralMateria for (tenant_id, materia_id, asignacion_id=null)
- **WHEN** performing an upsert for the same key with new umbral_pct=80
- **THEN** the existing record SHALL be updated to umbral_pct=80

#### Scenario: Validate umbral_pct range
- **WHEN** attempting to set umbral_pct outside 1–100 range
- **THEN** a validation error SHALL be raised

#### Scenario: Tenant isolation for umbral materia
- **GIVEN** UmbralMaterias in two different tenants
- **WHEN** querying by materia_id
- **THEN** only the record belonging to the correct tenant SHALL be returned
