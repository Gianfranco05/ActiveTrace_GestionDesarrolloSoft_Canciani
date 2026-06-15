## ADDED Requirements

### Requirement: Asignacion ORM model (Usuario ↔ Rol ↔ academic context)

The system SHALL define an Asignacion ORM model linking a Usuario to a Rol within an optional academic context (Materia, Carrera, Cohorte, comisiones) with temporal vigencia. The model SHALL extend BaseModelMixin.

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK, via BaseModelMixin |
| `tenant_id` | UUID | FK → Tenant(id), via BaseModelMixin |
| `usuario_id` | UUID | FK → Usuario(id), NOT NULL |
| `rol_id` | UUID | FK → Rol(id), NOT NULL — from C-04 |
| `materia_id` | UUID | FK → Materia(id), nullable |
| `carrera_id` | UUID | FK → Carrera(id), nullable |
| `cohorte_id` | UUID | FK → Cohorte(id), nullable |
| `comisiones` | Text | nullable — JSON string or comma-separated list |
| `responsable_id` | UUID | FK → Asignacion(id), nullable — self-referential |
| `vig_desde` | Date | NOT NULL |
| `vig_hasta` | Date | nullable = open-ended |
| `created_at` | DateTime | via BaseModelMixin |
| `updated_at` | DateTime | via BaseModelMixin |
| `deleted_at` | DateTime | nullable, via BaseModelMixin |

**estado_vigencia is DERIVED** (NOT stored):

```python
@property
def estado_vigencia(self) -> str:
    today = date.today()
    if self.vig_desde <= today and (self.vig_hasta is None or self.vig_hasta >= today):
        return "Vigente"
    return "Vencida"
```

**Unique constraint**: `(usuario_id, rol_id, materia_id, carrera_id, cohorte_id)` with partial index `WHERE deleted_at IS NULL`.

#### Scenario: Create asignacion with valid fields
- **WHEN** creating an Asignacion with usuario_id, rol_id, vig_desde
- **THEN** the Asignacion SHALL have a UUID id, all provided fields, created_at, updated_at

#### Scenario: Asignacion estado_vigencia is Vigente when within range
- **WHEN** vig_desde <= today AND (vig_hasta IS NULL OR vig_hasta >= today)
- **THEN** estado_vigencia SHALL return "Vigente"

#### Scenario: Asignacion estado_vigencia is Vencida when outside range
- **WHEN** vig_desde > today OR vig_hasta < today
- **THEN** estado_vigencia SHALL return "Vencida"

#### Scenario: Asignacion unique constraint per context
- **WHEN** creating a second Asignacion with the same usuario_id, rol_id, materia_id, carrera_id, cohorte_id
- **THEN** an IntegrityError SHALL be raised

#### Scenario: Asignacion allows multiple active assignments for different contexts
- **WHEN** creating Asignaciones with the same usuario_id but different rol_id or context
- **THEN** all creations SHALL succeed

#### Scenario: Asignacion nullable academic context
- **WHEN** creating an Asignacion without materia_id, carrera_id, cohorte_id
- **THEN** those fields SHALL be NULL

#### Scenario: Asignacion self-referential responsable
- **WHEN** creating an Asignacion with responsable_id pointing to another Asignacion
- **THEN** the FK constraint SHALL be enforced

#### Scenario: Asignacion soft delete
- **WHEN** calling soft_delete on an Asignacion
- **THEN** deleted_at SHALL be set to the current timestamp (not hard deleted)

#### Scenario: Asignacion FK to usuario enforced
- **WHEN** creating an Asignacion with a non-existent usuario_id
- **THEN** an IntegrityError SHALL be raised

#### Scenario: Asignacion FK to rol enforced
- **WHEN** creating an Asignacion with a non-existent rol_id
- **THEN** an IntegrityError SHALL be raised

#### Scenario: Asignacion FK to materia is nullable
- **WHEN** creating an Asignacion with a non-existent materia_id
- **THEN** an IntegrityError SHALL be raised
- **WHEN** creating an Asignacion with materia_id = NULL
- **THEN** the creation SHALL succeed

### Requirement: AsignacionRepository

The system SHALL provide an AsignacionRepository extending BaseRepository[Asignacion] with:

- All BaseRepository methods (list, get, create, update, soft_delete)
- `get_by_usuario(usuario_id: UUID) -> list[Asignacion]` — find all assignments for a user
- `get_activas_by_usuario(usuario_id: UUID) -> list[Asignacion]` — only currently vigente assignments

#### Scenario: Get asignaciones by usuario
- **WHEN** calling get_by_usuario with an existing usuario_id
- **THEN** all Asignaciones for that usuario SHALL be returned

#### Scenario: Get activas by usuario filters by vigencia
- **WHEN** calling get_activas_by_usuario with a usuario_id
- **THEN** only Asignaciones where vig_desde <= today AND (vig_hasta IS NULL OR vig_hasta >= today) SHALL be returned

#### Scenario: Asignacion list excludes soft-deleted
- **WHEN** calling list() after soft-deleting an Asignacion
- **THEN** the result SHALL NOT include the soft-deleted Asignacion

### Requirement: Asignacion schemas

**AsignacionCreate**:
- usuario_id (UUID), rol_id (UUID), materia_id (UUID?, default None), carrera_id (UUID?, default None), cohorte_id (UUID?, default None), comisiones (str?, default None), responsable_id (UUID?, default None), vig_desde (date), vig_hasta (date?, default None)
- `model_config = ConfigDict(extra='forbid')`

**AsignacionUpdate**:
- All fields optional: usuario_id?, rol_id?, materia_id?, carrera_id?, cohorte_id?, comisiones?, responsable_id?, vig_desde?, vig_hasta?
- `model_config = ConfigDict(extra='forbid')`

**AsignacionResponse**:
- id, tenant_id, usuario_id, rol_id, materia_id?, carrera_id?, cohorte_id?, comisiones?, responsable_id?, vig_desde, vig_hasta?, estado_vigencia (str — DERIVED), created_at, updated_at
- `model_config = ConfigDict(from_attributes=True, extra='forbid')`

#### Scenario: AsignacionCreate rejects extra fields
- **WHEN** passing an unknown field to AsignacionCreate
- **THEN** a validation error SHALL be raised

#### Scenario: AsignacionResponse includes estado_vigencia
- **WHEN** serializing an Asignacion to AsignacionResponse
- **THEN** estado_vigencia SHALL be present and SHALL be either "Vigente" or "Vencida"
