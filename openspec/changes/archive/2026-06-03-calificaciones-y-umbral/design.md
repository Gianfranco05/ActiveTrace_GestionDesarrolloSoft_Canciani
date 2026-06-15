## Context

C-09 delivered the versioned student roster (VersionPadron + EntradaPadron), which provides the data backbone for grade tracking. C-10 builds on top of that foundation to add the Calificacion model (per-alumno grade entries) and UmbralMateria configuration.

The KB defines E7 (Calificacion) and E8 (UmbralMateria) with specific derivation rules: `aprobado` is a derived boolean computed at import time based on the active umbral threshold. A critical business rule is that modifying the umbral later MUST NOT retroactively change existing grades — `aprobado` is frozen at import time.

Governance is **MEDIO** — standard domain logic, no security invariants, no auth flow modification. Import file parsing extends the Moodle export format patterns from C-09.

Key references:
- KB §E7 Calificacion: entrada_padron_id FK, nota_numerica/nota_textual, aprobado derivado, origen (Importado/Manual)
- KB §E8 UmbralMateria: umbral_pct (default 60%), valores_aprobatorios
- KB F1.1: Importar calificaciones (preview → confirm)
- KB F1.2: Reporte de finalización (detectar TPs sin corregir)
- KB F2.1: Configurar umbral de aprobación
- KB FL-02 pasos 3–5: flujo central del profesor
- RN-01: Columnas (Real) = nota numérica
- RN-02: Valores textuales aprobatorios
- RN-03: Umbral por defecto 60%

## Goals / Non-Goals

**Goals:**
- Calificacion ORM model with derived aprobado (frozen at import time)
- UmbralMateria ORM model with configurable threshold (default 60%)
- CalificacionRepository for bulk import and query operations
- UmbralRepository for get/upsert operations
- Grade file parser that detects numeric activities (columns ending in `(Real)`) and textual activities
- Import service: upload → preview (detect activities, show sample rows) → confirm (create Calificacion records, derive aprobado, audit)
- Reporte de finalización (F1.2): cross-reference completion file vs existing grades, detect "posibles entregas sin corregir"
- Umbral service: get current umbral for materia, set/update umbral
- Pydantic schemas for all request/response payloads
- Calificaciones router with import preview, confirm, reporte-finalizacion, get/set umbral endpoints
- Alembic migration 008
- Soft delete on all models via BaseModelMixin
- Audit: CALIFICACIONES_IMPORTAR already exists in AuditAction enum

**Non-Goals:**
- C-11: Análisis de atrasados (consumes grade data, built on top)
- C-12: Comunicaciones (built on top of C-11)
- Retroactive recalculation of aprobado when umbral changes (explicitly excluded per RN-03/domain rule)
- Frontend UI for import flow or umbral configuration — deferred to later changes
- Edición manual de calificaciones individuales (origen=Manual is structural, not implemented)
- Grade export or bulk download
- Per-activity-type umbral (single umbral per materia)

## Decisions

### D1 — Calificacion model: aprobado is stored, not computed at query time

Aprobado is a stored boolean column, set at import time based on the active umbral. It is NOT computed dynamically on read.

```python
class Calificacion(BaseModelMixin, Base):
    __tablename__ = "calificacion"

    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materia.id"), nullable=False)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cohorte.id"), nullable=False)
    entrada_padron_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entrada_padron.id"), nullable=False)
    actividad: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # "Numerica" | "Textual"
    nota_numerica: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    nota_textual: Mapped[str | None] = mapped_column(Text, nullable=True)
    aprobado: Mapped[bool] = mapped_column(Boolean, nullable=False)
    origen: Mapped[str] = mapped_column(String(20), nullable=False, default="Importado")  # Importado | Manual
    importado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
```

**Why stored not computed?** RN-03 explicitly states that changing the umbral should NOT affect existing grades. If aprobado were computed at query time, changing the umbral would retroactively change whether a grade is considered passing — violating the requirement. Storing the derived value at import time freezes it.

**Alternative considered:** DB-generated column (computed column). Rejected because the derivation logic depends on NOTA_NUMERICA vs NOTA_TEXTUAL branching which is non-trivial in pure SQL, and stored boolean is simpler and testable.

### D2 — RN-04 scope isolation for grade import

Unlike the padrón (which is per materia×cohorte), grades are scoped to `(usuario_id × materia_id)`. This means:
- Teacher A imports grades for Materia X → only Teacher A sees those grades
- Teacher B also imports grades for Materia X → independent set, not visible to Teacher A
- A COORDINADOR can see ALL grades for any materia

Implementation: Calificacion model stores `cargado_por` (FK → Usuario). Repository methods accept an optional `cargado_por` filter. Endpoints for PROFESOR scope by their own usuario_id; COORDINADOR endpoints can omit the filter.

**Why scope isolation matters:** Multiple teachers can share a materia (different comisiones). RN-04 ensures vaciado/import scope isolation. This is DIFFERENT from the padrón model where one active version replaces the previous one.

### D3 — Two-phase import flow (same pattern as C-09)

```
POST /api/calificaciones/importar/preview     → Parse file, detect columns, return preview
POST /api/calificaciones/importar/confirmar    → Create Calificacion records
POST /api/calificaciones/importar/reporte-finalizacion → Cross-reference completion data
```

**Phase 1 — Preview (idempotent, no side effects):**
1. Receive uploaded file (.xlsx or .csv)
2. Detect format (extension + MIME)
3. Parse headers → identify activity columns:
   - Columns ending in `(Real)` → type=Numeric
   - All other non-identifying columns → type=Textual
   - Identifying columns (nombre, apellidos, email, comision) → NOT activities
4. Read first N rows (default 20)
5. Return preview with: detected activities (name + type), total_rows, sample rows

**Phase 2 — Confirm:**
1. Client re-uploads file + sends `{actividad_mapping: {columna_header: nombre_actividad}}`
2. For each row + each activity column:
   a. Find matching EntradaPadron by (nombre, apellidos, email) or navigate from pre-linked entries
   b. Determine tipo from column classification
   c. Parse value: Numeric → Decimal; Textual → string
   d. Compute aprobado based on current UmbralMateria for this materia
   e. Create Calificacion record
3. Audit log: `CALIFICACIONES_IMPORTAR` with `actividades_count`, `filas_afectadas`

**Same re-upload approach as C-09.** No temp file storage — client re-uploads on confirm. Stateless and simple.

### D4 — Activity column detection (RN-01, RN-02)

The file parser distinguishes identifying columns from activity columns:
- **Identifying columns**: nombre, apellidos, email, comision, regional (same normalization as C-09)
- **Numeric activities**: columns whose header ends in `(Real)` (case-insensitive, trimmed)
- **Textual activities**: all other non-identifying columns

```python
@dataclass
class DetectedActivity:
    header: str          # original column header
    nombre: str          # cleaned activity name (without (Real) suffix)
    tipo: str            # "Numerica" | "Textual"
```

Preview returns the detected activities list for the user to confirm or rename.

### D5 — UmbralMateria model

```python
class UmbralMateria(BaseModelMixin, Base):
    __tablename__ = "umbral_materia"

    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materia.id"), nullable=False)
    asignacion_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("asignacion.id"), nullable=True)
    umbral_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    valores_aprobatorios: Mapped[list[str]] = mapped_column(postgresql.ARRAY(String), nullable=False, default=["Satisfactorio", "Supera lo esperado"])
```

**Rules:**
- One UmbralMateria per (materia_id, asignacion_id) — unique constraint. Null asignacion_id means tenant default.
- `umbral_pct` validated 1–100
- `valores_aprobatorios` default: ["Satisfactorio", "Supera lo esperado"] per RN-02
- If no UmbralMateria exists for a materia, default umbral_pct = 60

**Deviation from KB E8:** KB shows UmbralMateria FK to Asignacion, meaning per-teacher thresholds. For C-10 we simplify to one umbral per materia (asignacion_id is reserved for future per-teacher override). The KB F2.1 says "docente define el porcentaje" which implies per-materia (configured by whoever teaches it). If multiple teachers share a materia, they share the threshold. Per-teacher thresholds can be added later via asignacion_id.

### D6 — Umbral changes do NOT retroactively affect grades

This is a hard domain rule (derived from RN-03 intent):
- When importing grades, the CURRENT UmbralMateria config determines `aprobado`
- Changing UmbralMateria later does NOT update existing Calificacion records
- The stored `aprobado` column is the source of truth for "was this grade passing at import time"

This is why D1 stores `aprobado` rather than computing it.

### D7 — Reporte de finalización (F1.2, RN-07, RN-08)

```
POST /api/calificaciones/importar/reporte-finalizacion
```

Purpose: Detect TPs that students submitted but that haven't been graded yet.

1. Receive uploaded completion report file (.xlsx/.csv) with columns:
   - Identifying: nombre, apellidos (required)
   - Activity columns: same as grade file, but values indicate completion status (e.g., "Entregado", "No entregado")
2. For each activity column:
   - Only process columns classified as Textual (per RN-08: "solo actividades de escala textual")
   - Skip Numeric columns (absence of numeric grade = not submitted, not pending review)
3. For each student × textual activity:
   - Check if there's an existing Calificacion record with aprobado=True or nota_textual is set
   - If the completion status is "Entregado" (or similar "submitted" indicator) AND no Calificacion exists → flag as "posible entrega sin corregir"
4. Return grouped list: `{actividad: str, alumnos: [{nombre, apellidos, email}]}`

**Why only textual?** RN-08: numeric activities without a grade means the student didn't submit. Textual activities without a grade means the teacher hasn't reviewed it yet — the student DID submit (completion report confirms delivery).

### D8 — Schemas

```python
class CalificacionResponse(BaseModel):
    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    entrada_padron_id: UUID
    actividad: str
    tipo: str
    nota_numerica: Decimal | None
    nota_textual: str | None
    aprobado: bool
    origen: str
    importado_at: datetime
    model_config = ConfigDict(from_attributes=True, extra='forbid')

class UmbralResponse(BaseModel):
    materia_id: UUID
    asignacion_id: UUID | None
    umbral_pct: int
    valores_aprobatorios: list[str]
    model_config = ConfigDict(from_attributes=True, extra='forbid')

class UmbralUpdateRequest(BaseModel):
    materia_id: UUID
    umbral_pct: int = Field(default=60, ge=1, le=100)
    valores_aprobatorios: list[str] | None = None
    model_config = ConfigDict(extra='forbid')

class ActividadDetectada(BaseModel):
    header: str
    nombre: str
    tipo: str  # "Numerica" | "Textual"
    model_config = ConfigDict(extra='forbid')

class ImportPreviewResponse(BaseModel):
    filename: str
    total_rows: int
    preview_rows: list[dict]
    actividades_detectadas: list[ActividadDetectada]
    model_config = ConfigDict(extra='forbid')

class ImportConfirmRequest(BaseModel):
    filename: str
    materia_id: UUID
    cohorte_id: UUID
    actividad_mapping: dict[str, str] | None = None  # {header: nombre_actividad} override
    model_config = ConfigDict(extra='forbid')

class ImportConfirmResponse(BaseModel):
    materia_id: UUID
    cohorte_id: UUID
    calificaciones_creadas: int
    model_config = ConfigDict(extra='forbid')

class ReporteAlumno(BaseModel):
    nombre: str
    apellidos: str
    email: str | None
    model_config = ConfigDict(extra='forbid')

class ReporteActividadSinCorregir(BaseModel):
    actividad: str
    alumnos: list[ReporteAlumno]
    model_config = ConfigDict(extra='forbid')

class ReporteFinalizacionResponse(BaseModel):
    filename: str
    total_actividades_revisadas: int
    posibles_sin_corregir: list[ReporteActividadSinCorregir]
    model_config = ConfigDict(extra='forbid')
```

### D9 — Router structure

| Method | Path | Guard | Description |
|--------|------|-------|-------------|
| POST | `/api/calificaciones/importar/preview` | `calificaciones:cargar` | Upload file, return detected activities + preview rows |
| POST | `/api/calificaciones/importar/confirmar` | `calificaciones:cargar` | Confirm import, create Calificacion records |
| POST | `/api/calificaciones/importar/reporte-finalizacion` | `calificaciones:cargar` | Upload completion report, detect TPs sin corregir |
| GET | `/api/calificaciones/umbral` | `calificaciones:ver` | Get umbral for materia (query param: materia_id) |
| PUT | `/api/calificaciones/umbral` | `calificaciones:cargar` | Set or update umbral for materia |

**Permission notes:**
- `calificaciones:cargar` and `calificaciones:ver` are NEW permissions that must be created in the permission catalog
- PROFESOR scope: their own usuario_id filters Calificacion queries
- COORDINADOR scope: no filtering — sees all

### D10 — Repository design

**CalificacionRepository:**
```python
class CalificacionRepository:
    async def bulk_create(self, calificaciones: list[dict]) -> list[Calificacion]: ...
    async def get_by_materia_y_cohorte(
        self, materia_id: UUID, cohorte_id: UUID,
        cargado_por: UUID | None = None,
        offset: int = 0, limit: int = 100
    ) -> tuple[list[Calificacion], int]: ...
    async def get_by_entrada_padron(
        self, entrada_padron_id: UUID, actividad: str
    ) -> Calificacion | None: ...
    async def count_by_actividad(
        self, materia_id: UUID, cohorte_id: UUID, actividad: str
    ) -> int: ...
```

**UmbralRepository:**
```python
class UmbralRepository:
    async def get_by_materia(self, materia_id: UUID) -> UmbralMateria | None: ...
    async def upsert(self, materia_id: UUID, data: dict) -> UmbralMateria: ...
```

### D11 — Aprobado derivation logic

```python
def compute_aprobado(
    tipo: str,
    nota_numerica: Decimal | None,
    nota_textual: str | None,
    umbral_materia: UmbralMateria | None,
) -> bool:
    umbral_pct = (umbral_materia.umbral_pct if umbral_materia else 60) / 100
    valores_aprobatorios = (
        umbral_materia.valores_aprobatorios
        if umbral_materia and umbral_materia.valores_aprobatorios
        else ["Satisfactorio", "Supera lo esperado"]
    )

    if tipo == "Numerica":
        if nota_numerica is None:
            return False
        # Normalize: assume max score is 100 (or percentage-based)
        return nota_numerica >= umbral_pct * 100  # umbral_pct is already 1-100, so compare raw
    else:  # Textual
        if nota_textual is None:
            return False
        return nota_textual.strip().lower() in [v.strip().lower() for v in valores_aprobatorios]
```

Note: The comparison assumes grades are on a 0-100 scale (or the max score maps to 100). If grades are on a different scale, the normalization is deferred to C-10 implementation review.

### D12 — Migration 008 structure

```python
# 008_calificaciones_y_umbral.py
# Creates:
#   - calificacion (id UUID PK, tenant_id FK → tenant, materia_id FK → materia,
#     cohorte_id FK → cohorte, entrada_padron_id FK → entrada_padron,
#     actividad String(200) NOT NULL, tipo String(20) NOT NULL,
#     nota_numerica Numeric(5,2) nullable, nota_textual Text nullable,
#     aprobado Boolean NOT NULL, origen String(20) NOT NULL default 'Importado',
#     cargado_por UUID FK → usuario, importado_at DateTime,
#     created_at, updated_at, deleted_at)
#   - umbral_materia (id UUID PK, tenant_id FK → tenant, materia_id FK → materia,
#     asignacion_id FK → asignacion nullable, umbral_pct Integer NOT NULL default 60,
#     valores_aprobatorios ARRAY(String) NOT NULL default [],
#     created_at, updated_at, deleted_at)
# Indexes:
#   - IX calificacion: (materia_id, cohorte_id)
#   - IX calificacion: (entrada_padron_id)
#   - IX calificacion: (cargado_por)
#   - UNIQUE umbral_materia: (tenant_id, materia_id, asignacion_id) WHERE deleted_at IS NULL
```

## Risks / Trade-offs

- **[Grade scope isolation vs RN-04]** → RN-04 says "vaciado elimina solo datos del usuario que lo ejecuta". This means the model must store who imported each grade. D2 captures this with `cargado_por`. Trade-off: COORDINADOR queries need UNION-like logic across importers.
- **[Umbral per materia vs per teacher]** → KB E8 shows FK to Asignacion (per-teacher). D5 simplifies to per-materia for C-10. If per-teacher thresholds are needed later, adding asignacion_id to the unique constraint is straightforward. Trade-off: teachers sharing a materia share the threshold.
- **[File re-upload on confirm]** → Same trade-off as C-09. No temp state, but larger files increase request size. Acceptable for grade files (<1MB typical).
- **[Stored aprobado vs computed]** → D1 stores aprobado. This means existing grades are NOT affected by umbral changes — which is the requirement. Trade-off: if business rules change to require retroactive recalculation, a migration script would need to recompute all rows.
- **[New permissions calificaciones:cargar and calificaciones:ver]** → These must be seeded in the RBAC system. If not already auto-created by the permiso seeding script, the migration or a data migration must create them.
- **[Grade file column name normalization]** → Column naming in Moodle exports may vary. The parser must be lenient (case-insensitive, trim spaces, normalize Unicode) but explicit enough to avoid false positives. RN-01 defines `(Real)` suffix for numeric columns — this is the anchor.

## Migration Plan

1. Implement Calificacion model in `models/calificacion.py`
2. Implement UmbralMateria model in same file
3. Implement Pydantic schemas in `schemas/calificacion.py`
4. Implement UmbralRepository in `repositories/umbral_repository.py`
5. Implement CalificacionRepository in `repositories/calificacion_repository.py`
6. Implement grade file parser (extend or separate from C-09 file_parser)
7. Implement UmbralService in `services/umbral_service.py`
8. Implement CalificacionService in `services/calificacion_service.py` (import flow + reporte-finalizacion)
9. Implement calificaciones router in `api/v1/routers/calificaciones.py` + register in main.py
10. Generate Alembic migration 008
11. Seed `calificaciones:cargar` and `calificaciones:ver` permissions if not auto-created
12. Run full test suite (TDD per task)
