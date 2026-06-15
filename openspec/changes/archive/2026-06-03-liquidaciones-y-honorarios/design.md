## Context

C-07 delivered the user model with `facturador` flag and banking data (CBU, alias, banco). C-06 provided Cohorte and Materia models. C-08 completed the Asignacion model (docente ↔ materia/cohorte/rol/comisiones). The financial module (Épica 10) now builds on these foundations to determine how every docente is paid each month.

Governance is **CRÍTICO** — this domain handles liquidaciones de honorarios, which has direct financial and legal implications. Two open questions from the KB persist:

- **PA-22** (claves de Plus y mapeo a materias): unresolved. The exact set of Plus group keys and their mapping to materias is not defined. The design treats `grupo` as a free-text configurable key with a separate `GrupoMateria` mapping table for tenant configuration.
- **PA-24** (facturas asociadas a comisiones): unresolved. The design supports both per-cohorte and global facturas via an optional `cohorte_id` FK.
- **PA-23** (acumulación de Plus): RESOLVED. RN-33 and RN-34 state: `Σ(Plus(grupo, rol) × N_comisiones)` — accumulated N times. Confirmed by KB.

Key KB references: E17-E20, F10.1-F10.6, FL-08, RN-21-22, RN-31-40.

## Goals / Non-Goals

**Goals:**
- SalarioBase ORM model with temporal validity and unique-rol constraint
- SalarioPlus ORM model with (grupo, rol) key and accumulation per RN-33
- GrupoMateria mapping table to resolve which materias belong to which Plus group
- Liquidacion ORM model with stored base/plus/total and Abierta/Cerrada state machine
- Factura ORM model for facturante billing (Pendiente/Abonada)
- Liquidation calculation engine: resolve temporal validity for base and plus, apply RN-34 formula, segment NEXO and facturantes
- Salary grid ABM: full CRUD for SalarioBase and SalarioPlus
- Liquidacion API: calculate/view/close/history/export with KPI segmentation
- Factura API: CRUD with status transitions
- Alembic migration for all new tables
- Soft delete via BaseModelMixin on all models
- Audit: `LIQUIDACION_CERRAR` action code
- RBAC: `liquidaciones:ver`, `liquidaciones:calcular`, `liquidaciones:cerrar`, `liquidaciones:exportar`, `liquidaciones:configurar-salarios`

**Non-Goals:**
- Payment execution or bank integration (the system calculates amounts; actual payments are external)
- Tax withholding calculations (retenciones, impuestos)
- Per-docente configuration of Plus applicability (all docentes with the same rol/grupo get the same Plus)
- Automatic recalculation when salary grid changes (historic liquidations are frozen)
- Edición manual de liquidación individual (calculated by system, bulk-close only)
- Frontend UI — C-21 will build the React frontend later

## Decisions

### D1 — SalarioBase: temporal validity with UNIQUE constraint on (tenant_id, rol)

```python
class SalarioBase(BaseModelMixin, Base):
    __tablename__ = "salario_base"

    rol: Mapped[str] = mapped_column(String(30), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "rol",
            name="uq_salario_base_rol",
        ),
    )
```

**Rules:**
- `rol` is an enum string matching Asignacion roles: PROFESOR, TUTOR, NEXO, COORDINADOR
- A NULL `vig_hasta` means the entry is valid indefinitely from `vig_desde`
- The UNIQUE constraint ensures exactly one entry per rol. To change the salary, FINANZAS updates the existing entry with new `vig_desde`/`vig_hasta` dates — the repository upserts and the historical entry's `vig_hasta` is set to the day before the new entry starts.
- The `monto` is the monthly base salary for that rol.

**Why UNIQUE per rol?** The KB says "solo puede haber una entrada vigente por rol en un instante dado". A single-entry-per-rol model with versioned vig_desde simplifies queries. To get the salary for a period, filter by `vig_desde <= periodo AND (vig_hasta IS NULL OR vig_hasta >= periodo)`.

**Alternative considered:** History table with multiple entries per rol, auto-versioned. Rejected: adds complexity without adding value since the KB requires exactly one active entry. The update pattern (set vig_hasta on old entry, insert new entry) handles history implicitly if needed.

### D2 — SalarioPlus: (grupo, rol) key with temporal validity

```python
class SalarioPlus(BaseModelMixin, Base):
    __tablename__ = "salario_plus"

    grupo: Mapped[str] = mapped_column(String(50), nullable=False)
    rol: Mapped[str] = mapped_column(String(30), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(200), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "grupo", "rol",
            name="uq_salario_plus_grupo_rol",
        ),
    )
```

**Rules:**
- `grupo` is a free-text string (e.g., "PROG", "BD", "ING"). This is configurable by tenant since PA-22 is unresolved.
- Same temporal validity pattern as SalarioBase.
- The `monto` is the per-comision amount — accumulated across comisiones per RN-33.

**Alternative considered:** Separate `GrupoPlus` catalog entity. Rejected: the grupo key is a simple string label; a separate table adds indirection without benefit at this stage. When PA-22 resolves, the grupo values can be seeded from a config file or manage from the ABM UI.

### D3 — GrupoMateria mapping table (PA-22 mitigation)

```python
class GrupoMateria(BaseModelMixin, Base):
    __tablename__ = "grupo_materia"

    grupo: Mapped[str] = mapped_column(String(50), nullable=False)
    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materia.id"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "grupo", "materia_id",
            name="uq_grupo_materia",
        ),
    )
```

This enables FINANZAS to configure which materias belong to which Plus group. Without this mapping, the system cannot determine which Plus applies to a docente's comisiones. The calculation engine resolves: for each comision → materia → grupo → SalarioPlus.

**Alternative considered:** Hardcoded mapping in config file. Rejected: the mapping should be tenant-administrable without code changes, and PA-22 explicitly asks whether it's configurable per tenant.

### D4 — Liquidacion: stored values, state machine, (cohorte, periodo) unit

```python
class Liquidacion(BaseModelMixin, Base):
    __tablename__ = "liquidacion"

    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cohorte.id"), nullable=False
    )
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)  # "YYYY-MM"
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id"), nullable=False
    )
    rol: Mapped[str] = mapped_column(String(30), nullable=False)
    comisiones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    monto_base: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    monto_plus: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    es_nexo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    excluido_por_factura: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Abierta"
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "cohorte_id", "periodo", "usuario_id",
            name="uq_liquidacion_periodo_docente",
        ),
    )
```

**Key decisions:**
- **Stored total**: `monto_base`, `monto_plus`, and `total` are stored Decimal columns, not computed at query time. When a liquidacion is calculated and then closed, the values are frozen. Changing the salary grid later does NOT retroactively affect closed liquidaciones. This is the same pattern as `Calificacion.aprobado` being stored.
- **State machine**: Abierta → Cerrada. Once Cerrada, updates are forbidden except soft-delete (audited). No reverse transition.
- **Unit**: `(cohorte_id, periodo, usuario_id)` is unique per RN-37. One liquidation line per docente per period per cohorte.
- **es_nexo**: Default False. Set True when the docente's rol in the liquidation is NEXO (RN-36).
- **excluido_por_factura**: Default False. Set True when `usuario.facturador == True` (RN-35).
- **comisiones**: Text field with serialized list of comision names, for display purposes.

### D5 — Calculation engine: temporal validity resolution + RN-34

The calculation flow for a given `(cohorte_id, periodo)`:

```
1. Determine month boundaries from "YYYY-MM" string
2. Query all Asignacion records active in that cohorte:
   WHERE cohorte_id = X AND vig_desde <= mes_end AND (vig_hasta IS NULL OR vig_hasta >= mes_start)
3. Group by usuario_id → determine the rol for liquidation
4. For each (usuario, rol, comisiones):
   a. Look up SalarioBase WHERE rol = X AND vig_desde <= mes_start AND (vig_hasta IS NULL OR vig_hasta >= mes_start)
   b. Get the lista of materias for that docente's comisiones
   c. For each materia, look up GrupoMateria to get grupo
   d. For each grupo, look up SalarioPlus WHERE grupo = X AND rol = X AND valid for period
   e. Count N_comisiones per grupo (how many comisiones of that grupo)
   f. monto_plus = Σ(plus.monto × N_comisiones_per_grupo)
   g. total = monto_base + monto_plus
   h. Set es_nexo = (rol == "NEXO")
   i. Set excluido_por_factura = (usuario.facturador == True)
5. Create/update Liquidacion records for each docente
6. Return Liquidacion list
```

**Temporal validity query pattern:**
```python
def is_active_in_period(desde: date, hasta: Optional[date], mes_start: date) -> bool:
    return desde <= mes_start and (hasta is None or hasta >= mes_start)
```

**Edge cases:**
- If no SalarioBase exists for a rol → exclude docente from liquidation (or default to 0 and flag)
- If a materia has no GrupoMateria mapping → it doesn't contribute to any Plus (0 additional)
- If a docente has no Asignacion active in that cohorte → they don't appear in liquidation
- If usuario.facturador is True → still create a Liquidacion record but with `excluido_por_factura=True`, `total=0`. The facturante's payment is handled by Factura module.

### D6 — Liquidation close: inmutable after close

```python
async def cerrar_liquidacion(cohorte_id: UUID, periodo: str, actor_id: UUID) -> list[Liquidacion]:
    # 1. Verify all Liquidacion records for (cohorte, periodo) exist and are Abierta
    # 2. Transition estado: Abierta → Cerrada on all records in bulk
    # 3. Audit log: LIQUIDACION_CERRAR, filas_afectadas = count
    # 4. Return updated records
```

RN-22: "Al ejecutar el cierre de una liquidación, su contenido queda inmutabilizado". This means after close:
- UPDATE on any field (except soft-delete) returns 403 or is blocked at the service layer
- The repository checks `if liquidacion.estado == "Cerrada": raise CannotModifyClosedLiquidationError`

### D7 — Factura model

```python
class Factura(BaseModelMixin, Base):
    __tablename__ = "factura"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id"), nullable=False
    )
    cohorte_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("cohorte.id"), nullable=True
    )
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)
    detalle: Mapped[str] = mapped_column(Text, nullable=False)
    referencia_archivo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tamano_kb: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Pendiente"
    )
    cargada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc),
    )
    abonada_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

**Rules (RN-39, RN-40):**
- Estado: Pendiente ↔ Abonada (two states, bidirectional)
- `abonada_at` is set automatically when transitioning to Abonada
- `cohorte_id` is optional per PA-24 — allows both per-cohorte and global facturas
- `referencia_archivo` is an opaque pointer (key/URL) to the file storage service, not a filesystem path
- Only usuarios with `facturador=True` should appear in factura management (validated at service layer)

### D8 — Router structure

**Liquidaciones router** (`/api/liquidaciones`):

| Method | Path | Guard | Description |
|--------|------|-------|-------------|
| GET | `/` | `liquidaciones:ver` | List liquidaciones with filters (cohorte_id, periodo, docente_id) |
| POST | `/calcular` | `liquidaciones:calcular` | Trigger calculation for (cohorte_id, periodo) |
| POST | `/{cohorte_id}/{periodo}/cerrar` | `liquidaciones:cerrar` | Close all liquidaciones for the period |
| GET | `/historial` | `liquidaciones:ver` | List closed liquidaciones from previous periods |
| GET | `/exportar` | `liquidaciones:exportar` | Export liquidacion as spreadsheet |

**Grilla salarial router** (merged into liquidaciones router):

| Method | Path | Guard | Description |
|--------|------|-------|-------------|
| GET | `/salarios/base` | `liquidaciones:ver` | List all SalarioBase entries |
| POST | `/salarios/base` | `liquidaciones:configurar-salarios` | Create/update SalarioBase |
| DELETE | `/salarios/base/{id}` | `liquidaciones:configurar-salarios` | Soft-delete SalarioBase |
| GET | `/salarios/plus` | `liquidaciones:ver` | List all SalarioPlus entries |
| POST | `/salarios/plus` | `liquidaciones:configurar-salarios` | Create/update SalarioPlus |
| DELETE | `/salarios/plus/{id}` | `liquidaciones:configurar-salarios` | Soft-delete SalarioPlus |
| GET | `/salarios/grupos` | `liquidaciones:ver` | List all GrupoMateria mappings |
| POST | `/salarios/grupos` | `liquidaciones:configurar-salarios` | Create GrupoMateria mapping |
| DELETE | `/salarios/grupos/{id}` | `liquidaciones:configurar-salarios` | Delete GrupoMateria mapping |

**Facturas router** (`/api/facturas`):

| Method | Path | Guard | Description |
|--------|------|-------|-------------|
| GET | `/` | `liquidaciones:ver` | List facturas with filters |
| POST | `/` | `liquidaciones:ver` | Create factura (register new billing document) |
| PUT | `/{id}/abonar` | `liquidaciones:ver` | Transition to Abonada |
| PUT | `/{id}/reabrir` | `liquidaciones:ver` | Transition back to Pendiente |
| DELETE | `/{id}` | `liquidaciones:ver` | Soft-delete factura |

**Permission notes:**
- All endpoints under `liquidaciones:*` are assigned to FINANZAS role. ADMIN also gets them (ADMIN has all permissions by default).
- `liquidaciones:configurar-salarios` is a separate, more sensitive permission for modifying the salary grid.
- Factura endpoints also use `liquidaciones:ver` since facturas are part of the financial module.

### D9 — KPI segmentation (RN-36, RN-38)

The liquidation view response includes KPI data:

```python
class LiquidacionKPIs(BaseModel):
    total_general: Decimal          # Sum of all liquidaciones (including NEXO)
    total_sin_factura: Decimal      # Sum excluding facturantes
    total_nexo: Decimal             # Sum of es_nexo=True entries
    total_facturantes: int          # Count of excluido_por_factura=True entries
    total_docentes: int             # Total docentes in liquidation
    model_config = ConfigDict(from_attributes=True, extra='forbid')
```

The list is segmented into three groups:
1. **General**: rows where `es_nexo=False AND excluido_por_factura=False`
2. **NEXO**: rows where `es_nexo=True`
3. **Facturantes**: rows where `excluido_por_factura=True`

RN-36: NEXO amounts are counted in the total general but displayed separately.
RN-38: "Total sin factura" and "Total con factura" KPIs.

### D10 — Schema design

Core request/response schemas (Pydantic v2, `extra='forbid'`, `from_attributes=True` on responses):

```python
# --- SalarioBase ---
class SalarioBaseCreate(BaseModel):
    rol: str = Field(min_length=1, max_length=30)
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    vig_desde: date
    vig_hasta: date | None = None
    model_config = ConfigDict(extra='forbid')

class SalarioBaseResponse(BaseModel):
    id: UUID
    rol: str
    monto: Decimal
    vig_desde: date
    vig_hasta: date | None
    model_config = ConfigDict(from_attributes=True, extra='forbid')

# --- SalarioPlus ---
class SalarioPlusCreate(BaseModel):
    grupo: str = Field(min_length=1, max_length=50)
    rol: str = Field(min_length=1, max_length=30)
    descripcion: str = Field(min_length=1, max_length=200)
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    vig_desde: date
    vig_hasta: date | None = None
    model_config = ConfigDict(extra='forbid')

class SalarioPlusResponse(BaseModel):
    id: UUID
    grupo: str
    rol: str
    descripcion: str
    monto: Decimal
    vig_desde: date
    vig_hasta: date | None
    model_config = ConfigDict(from_attributes=True, extra='forbid')

# --- Liquidacion ---
class LiquidacionResponse(BaseModel):
    id: UUID
    cohorte_id: UUID
    periodo: str
    usuario_id: UUID
    rol: str
    comisiones: str | None
    monto_base: Decimal
    monto_plus: Decimal
    total: Decimal
    es_nexo: bool
    excluido_por_factura: bool
    estado: str
    docente_nombre: str | None = None  # joined from Usuario
    docente_apellidos: str | None = None
    model_config = ConfigDict(from_attributes=True, extra='forbid')

class CalcularLiquidacionRequest(BaseModel):
    cohorte_id: UUID
    periodo: str = Field(pattern=r'^\d{4}-(0[1-9]|1[0-2])$')
    model_config = ConfigDict(extra='forbid')

class CerrarLiquidacionRequest(BaseModel):
    cohorte_id: UUID
    periodo: str = Field(pattern=r'^\d{4}-(0[1-9]|1[0-2])$')
    model_config = ConfigDict(extra='forbid')

class LiquidacionListResponse(BaseModel):
    liquidaciones: list[LiquidacionResponse]
    kpis: LiquidacionKPIs
    model_config = ConfigDict(extra='forbid')

# --- Factura ---
class FacturaCreate(BaseModel):
    usuario_id: UUID
    cohorte_id: UUID | None = None
    periodo: str = Field(pattern=r'^\d{4}-(0[1-9]|1[0-2])$')
    detalle: str = Field(min_length=1)
    referencia_archivo: str | None = None
    tamano_kb: Decimal | None = None
    model_config = ConfigDict(extra='forbid')

class FacturaResponse(BaseModel):
    id: UUID
    usuario_id: UUID
    cohorte_id: UUID | None
    periodo: str
    detalle: str
    referencia_archivo: str | None
    tamano_kb: Decimal | None
    estado: str
    cargada_at: datetime
    abonada_at: datetime | None
    model_config = ConfigDict(from_attributes=True, extra='forbid')

# --- GrupoMateria ---
class GrupoMateriaCreate(BaseModel):
    grupo: str = Field(min_length=1, max_length=50)
    materia_id: UUID
    model_config = ConfigDict(extra='forbid')

class GrupoMateriaResponse(BaseModel):
    id: UUID
    grupo: str
    materia_id: UUID
    model_config = ConfigDict(from_attributes=True, extra='forbid')
```

### D11 — Migration structure

```python
# 0NN_liquidaciones_y_honorarios.py
# Creates:
#   - salario_base (id UUID PK, tenant_id FK, rol String(30) NOT NULL,
#     monto Numeric(12,2) NOT NULL, vig_desde Date NOT NULL,
#     vig_hasta Date nullable, created_at, updated_at, deleted_at)
#   - salario_plus (id UUID PK, tenant_id FK, grupo String(50) NOT NULL,
#     rol String(30) NOT NULL, descripcion String(200) NOT NULL,
#     monto Numeric(12,2) NOT NULL, vig_desde Date NOT NULL,
#     vig_hasta Date nullable, created_at, updated_at, deleted_at)
#   - grupo_materia (id UUID PK, tenant_id FK, grupo String(50) NOT NULL,
#     materia_id FK → materia NOT NULL, created_at, updated_at, deleted_at)
#   - liquidacion (id UUID PK, tenant_id FK, cohorte_id FK → cohorte NOT NULL,
#     periodo String(7) NOT NULL, usuario_id FK → usuario NOT NULL,
#     rol String(30) NOT NULL, comisiones Text nullable,
#     monto_base Numeric(12,2) NOT NULL, monto_plus Numeric(12,2) NOT NULL DEFAULT 0,
#     total Numeric(12,2) NOT NULL, es_nexo Boolean NOT NULL DEFAULT false,
#     excluido_por_factura Boolean NOT NULL DEFAULT false,
#     estado String(20) NOT NULL DEFAULT 'Abierta',
#     created_at, updated_at, deleted_at)
#   - factura (id UUID PK, tenant_id FK, usuario_id FK → usuario NOT NULL,
#     cohorte_id FK → cohorte nullable, periodo String(7) NOT NULL,
#     detalle Text NOT NULL, referencia_archivo String(500) nullable,
#     tamano_kb Numeric(10,2) nullable,
#     estado String(20) NOT NULL DEFAULT 'Pendiente',
#     cargada_at DateTime NOT NULL, abonada_at DateTime nullable,
#     created_at, updated_at, deleted_at)
#
# ⚠️ PARTIAL UNIQUE INDEXES (soft-delete aware):
#   Since soft-deleted rows have deleted_at NOT NULL, we use PostgreSQL partial
#   unique indexes instead of standard UNIQUE constraints. SQLAlchemy's
#   UniqueConstraint does NOT support WHERE clauses — these must be created
#   via op.create_index() with postgresql_where in the migration:
#
#   op.create_index(
#       "uq_salario_base_rol",
#       "salario_base", ["tenant_id", "rol"],
#       unique=True,
#       postgresql_where=sa.text("deleted_at IS NULL"),
#   )
#   op.create_index(
#       "uq_salario_plus_grupo_rol",
#       "salario_plus", ["tenant_id", "grupo", "rol"],
#       unique=True,
#       postgresql_where=sa.text("deleted_at IS NULL"),
#   )
#   op.create_index(
#       "uq_grupo_materia",
#       "grupo_materia", ["tenant_id", "grupo", "materia_id"],
#       unique=True,
#       postgresql_where=sa.text("deleted_at IS NULL"),
#   )
#   op.create_index(
#       "uq_liquidacion_periodo_docente",
#       "liquidacion", ["tenant_id", "cohorte_id", "periodo", "usuario_id"],
#       unique=True,
#       postgresql_where=sa.text("deleted_at IS NULL"),
#   )
#
#   The ORM models do NOT declare UniqueConstraint in __table_args__ —
#   uniqueness is enforced at the DB level only. The repository layer
#   catches IntegrityError and raises domain-specific exceptions.
#
# Regular Indexes:
#   - IX liquidacion: (cohorte_id, periodo)
#   - IX liquidacion: (usuario_id)
#   - IX liquidacion: (estado)
#   - IX factura: (usuario_id, periodo)
#   - IX factura: (estado)
```

### D12 — File structure

```
backend/app/
├── models/
│   └── liquidacion.py          # SalarioBase, SalarioPlus, GrupoMateria, Liquidacion, Factura
├── schemas/
│   └── liquidacion.py          # All request/response DTOs
├── repositories/
│   ├── salario_repository.py   # SalarioBase + SalarioPlus + GrupoMateria queries
│   ├── liquidacion_repository.py  # Liquidacion queries + close
│   └── factura_repository.py   # Factura CRUD queries
├── services/
│   ├── liquidacion_service.py  # Calculation engine + close + segmentation
│   └── factura_service.py      # Factura CRUD + state transitions
├── api/v1/routers/
│   ├── liquidaciones.py        # /api/liquidaciones endpoints
│   └── facturas.py             # /api/facturas endpoints
├── core/
│   ├── audit_codes.py          # + LIQUIDACION_CERRAR
│   └── permissions.py          # + liquidaciones:* permissions
└── alembic/versions/
    └── 0NN_liquidaciones_y_honorarios.py

tests/
├── unit/
│   ├── test_liquidacion_service.py     # Calculation engine tests
│   └── test_factura_service.py         # Factura state machine tests
└── integration/
    ├── test_liquidaciones_api.py       # API endpoint tests
    └── test_facturas_api.py            # Factura API tests
```

### D13 — Recalculation semantics: upsert for Abierta, block for Cerrada

When FINANZAS calls `POST /api/liquidaciones/calcular` for the same `(cohorte_id, periodo)` twice:

**If existing liquidaciones are Abierta:**
- The calculation engine recalculates all amounts with current salary grid values
- Existing Liquidacion records are **updated in place** (UPSERT by `(tenant_id, cohorte_id, periodo, usuario_id)`)
- This allows correcting a liquidation before closing (e.g., salary grid was adjusted)

**If existing liquidaciones are Cerrada:**
- The operation is **blocked** with a 409 Conflict response
- RN-22: "Al ejecutar el cierre de una liquidación, su contenido queda inmutabilizado"
- If correction is needed, FINANZAS must handle it as a corrective entry outside the system

**If no existing liquidaciones:**
- New records are created (standard calculation flow)

**Implementation:**
```python
async def calcular_liquidacion(cohorte_id, periodo, tenant_id):
    existing = await repo.get_by_cohorte_periodo(cohorte_id, periodo)
    if existing and any(l.estado == "Cerrada" for l in existing):
        raise LiquidacionCerradaError("Cannot recalculate closed liquidation")
    # ... calculate amounts ...
    await repo.upsert_bulk(new_records, cohorte_id, periodo)
```

## Risks / Trade-offs

- **[CRÍTICO] PA-22 unresolved — Plus group keys and mapping**: The exact set of grupo keys is not defined. Decision: use free-text grupo string + GrupoMateria mapping table. FINANZAS configures materias per grupo via API/UI. Risk: if grupo keys have business meaning that affects the calculation formula beyond what RN-33/R-34 describe, the model may need adjustment. Mitigation: the GrupoMateria table is flexible; adding grupo-level metadata later is additive, not breaking.
- **[MEDIO] PA-24 unresolved — Factura ↔ Cohorte association**: Optional cohorte_id FK. If facturas must always be associated with a specific cohorte, the UI validation can enforce it without changing the model. Risk: low.
- **[MEDIO] SalarioBase UNIQUE per rol means one entry per rol ever**: When changing salary, the existing entry must be updated (vig_hasta set). If historical audit of salary changes is needed beyond what the audit log provides, this may be insufficient. Mitigation: the audit log records LIQUIDACION_CERRAR with all relevant context; if explicit salary version tracking is needed, a separate history table can be added.
- **[BAJO] Stored total frozen at close time — recalculate allowed while Abierta**: Liquidaciones Abiertas can be recalculated (upsert semantics per D13). Once Cerradas, values are immutable. If a Cerrada liquidation needs correction, FINANZAS handles it as a corrective entry outside the system. Mitigation: this matches real-world accounting immutability.
- **[BAJO] Facturante docentes still generate Liquidacion records**: With `total=0` and `excluido_por_factura=True`. This ensures the liquidation view shows them. If this is considered noise, it can be omitted with a filter. Mitigation: cheap records, useful for completeness.
- **[BAJO] Comisiones stored as Text (serialized list)**: Not normalized. If complex querying by individual comision is needed, a junction table would be required. Mitigation: the current KB pattern stores comisiones as a text field in Asignacion; matching this keeps consistency.

## Migration Plan

1. Add `LIQUIDACION_CERRAR` to audit codes enum
2. Add 5 new permissions to the permission catalog seed
3. Create Alembic migration 0NN with all 5 tables + indexes + unique constraints
4. Implement models in `models/liquidacion.py`
5. Implement schemas in `schemas/liquidacion.py`
6. Implement repositories (salario, liquidacion, factura)
7. Implement services (calculation engine + close + factura state machine)
8. Implement routers (liquidaciones, facturas) + register in main.py
9. Run full test suite (TDD per task) from `backend/`

## Open Questions

1. **PA-22** — What are the exact Plus group keys? **Resolved for C-18**: grupo is a free-text configurable key managed by FINANZAS via the GrupoMateria ABM. The initial seed will be empty — each tenant configures their own grupos. If standard keys are needed later, they can be seeded from a config file without model changes. See D3.
2. **PA-24** — Should facturas be linked to specific cohortes or are they global? **Resolved for C-18**: optional `cohorte_id` FK supports both. The business rule is left to the tenant/FINANZAS to decide per-factura. See D7.
3. **RN-26 enforcement** — Should the calculation engine skip docentes without banking data? **Resolved: YES.** The calculation engine skips docentes whose `usuario.cbu IS NULL AND usuario.alias_cbu IS NULL` per RN-26 ("Los datos bancarios/fiscales son requisito para ser liquidado"). Skipped docentes are reported in a `docentes_excluidos` list in the response with the reason "datos_bancarios_incompletos". See task 6.7.
4. **Recalculation semantics** — What happens when calculating the same (cohorte, periodo) twice? **Resolved: UPSERT for Abierta, BLOCK for Cerrada.** See D13.
