## Context

C-07 delivered Usuario (1:1 with AuthUser, PII encryption) and Asignacion (role assignments with temporal vigencia). C-06 delivered Carrera, Cohorte, Materia (academic structure with EstadoRegistro). C-05 delivered the append-only audit log. C-04 delivered RBAC with `require_permission`.

C-09 builds the **student roster foundation** — VersionPadron (versioned import header) and EntradaPadron (individual student entries per version). This is the data backbone for C-10 (calificaciones), C-11 (atrasados), and C-23 (comunicaciones).

The KB defines E6 with versioning rules: one active version per (materia_id, cohorte_id), activating a new version deactivates the previous one. EntradaPadron references Usuario but allows null (students who haven't created accounts yet).

Governance is **MEDIO** — standard domain logic, no security invariants, no auth flow modification. Integration with Moodle WS is new but follows the pattern of external service adapters.

## Goals / Non-Goals

**Goals:**
- VersionPadron ORM model with versioning rules (one active per materia×cohorte)
- EntradaPadron ORM model with encrypted email (reuse EncryptedString from C-07), nullable usuario_id
- PadronRepository for both models (they're intrinsically coupled)
- File parser: parse .xlsx and .csv into structured preview rows
- Moodle WS client with `get_enrolled_users()` method (mockable)
- Import service: parse → preview (dry-run) → confirm (write + audit)
- Vaciar (F1.5/RN-04): soft-delete entries for a non-active version only
- Pydantic schemas for all request/response payloads
- Padron router with import, preview, vaciar, list endpoints
- Alembic migration 007
- Soft delete on all models via BaseModelMixin
- Audit: PADRON_CARGAR already exists in AuditAction enum

**Non-Goals:**
- `get_grades()` in Moodle WS — C-10
- Sync nocturna / on-demand sync — C-10
- Frontend UI for the import flow — C-21 shell
- Any Calificacion model work — C-10
- Columna mapping customization in preview (accept what the file provides)
- Bulk export of padrón

## Decisions

### D1 — PadronRepository covers both models

VersionPadron and EntradaPadron are **intrinsically coupled**: every operation on a version affects its entries, and vice versa. A single `PadronRepository` handles both:

```python
class PadronRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def create_version(self, data: dict) -> VersionPadron: ...
    async def get_active_version(self, materia_id: UUID, cohorte_id: UUID) -> VersionPadron | None: ...
    async def deactivate_previous_active(self, materia_id: UUID, cohorte_id: UUID) -> None: ...
    async def create_entries(self, version_id: UUID, entries: list[dict]) -> list[EntradaPadron]: ...
    async def get_entries(self, version_id: UUID) -> list[EntradaPadron]: ...
    async def vaciar_entries(self, version_id: UUID) -> int: ...
    async def list_versions(self, materia_id: UUID, cohorte_id: UUID, offset: int, limit: int) -> tuple[list[VersionPadron], int]: ...
    async def get_version(self, version_id: UUID) -> VersionPadron | None: ...
```

**Why not separate repositories?** VersionPadron without EntradaPadron has no value, and EntradaPadron cannot exist without a VersionPadron. They form an aggregate. A single repository enforces consistency (e.g., vaciar only on non-active versions requires reading version state, which is natural in one class).

### D2 — Unique constraint for active version

```sql
CREATE UNIQUE INDEX ix_version_padron_unique_active
  ON version_padron (tenant_id, materia_id, cohorte_id)
  WHERE activa = true AND deleted_at IS NULL;
```

This ensures the business rule "one active version per materia×cohorte" is enforced at the DB level. The service layer also checks before activating, but the DB constraint prevents race conditions.

### D3 — EntradaPadron extends BaseModelMixin

Gets UUID PK, tenant_id, timestamps, soft delete. Fields:

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK via BaseModelMixin |
| `tenant_id` | UUID | FK → Tenant via BaseModelMixin |
| `version_id` | UUID | FK → VersionPadron.id, NOT NULL |
| `usuario_id` | UUID | FK → Usuario.id, NULLABLE |
| `nombre` | String(100) | Denormalized, NOT NULL |
| `apellidos` | String(150) | Denormalized, NOT NULL |
| `email` | Text | Encrypted via EncryptedString TypeDecorator |
| `comision` | String(50) | nullable |
| `regional` | String(100) | nullable |

**Why denormalized nombre/apellidos?** Historical accuracy. A student might change their name in AuthUser/Usuario after import. The padrón entry preserves the name as it was at import time — grades in C-10 reference EntradaPadron, so they always see the original enrollment name.

### D4 — Email encryption via EncryptedString TypeDecorator

Reuse the `EncryptedString` custom TypeDecorator from C-07 (`backend/app/core/encrypted_string.py`). Declare the field as:

```python
email: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
```

This means encryption/decryption happens transparently at the ORM level — no service-layer encrypt/decrypt needed for email. This is DIFFERENT from the Usuario PII approach (service-layer encrypt in C-07 D2) because email is encrypted at the type level, not the service level.

### D5 — Two-phase import flow

```
POST /api/v1/padron/importar/preview   → Parses file, returns preview
POST /api/v1/padron/importar/confirmar  → Creates version + entries
```

**Phase 1 — Preview (idempotent, no side effects):**
1. Receive uploaded file (.xlsx or .csv)
2. Detect format (extension + MIME)
3. Parse headers → auto-map columns: nombre, apellidos, email, comision, regional
4. Read first N rows (configurable, default 20)
5. Return preview with detected columns, row count, sample data

**Phase 2 — Confirm:**
1. User sends `{filename, column_mapping (optional override)}`
2. Service re-reads the file (stored temporarily or re-uploaded)
3. Validate minimum data (nombre, apellidos required)
4. Create VersionPadron with `activa=True`
5. Deactivate previous active version (if exists)
6. Bulk-create EntradaPadron rows
7. Audit log: `PADRON_CARGAR` with `filas_afectadas` count
8. Return VersionPadronResponse with entry count

**Alternative approach considered (temp storage):** Store the parsed preview in a temp table or cache between preview and confirm. Rejected because it adds state management complexity. Instead, the client re-uploads the file on confirm — simpler, stateless, and the file is small.

### D6 — Column mapping

The parser auto-detects columns by header name normalization:
- `nombre`, `name`, `nombres`, `alumno` → `nombre`
- `apellido`, `apellidos`, `apellido(s)`, `surname` → `apellidos`
- `email`, `e-mail`, `correo`, `mail` → `email`
- `comision`, `comisión`, `com`, `section` → `comision`
- `regional`, `sede`, `delegacion`, `delegación` → `regional`

The preview returns the detected mapping. The user can override it in the confirm request.

### D7 — Moodle WS client (mockable)

```python
# backend/app/integrations/moodle_ws.py
class MoodleWSClient:
    def __init__(self, base_url: str, token: str, timeout: int = 30):
        self._base_url = base_url
        self._token = token
        self._timeout = timeout

    async def get_enrolled_users(
        self, materia_id: str, cohorte_id: str
    ) -> list[MoodleStudent]:
        """Fetch enrolled students from Moodle via WS API.
        
        Returns list of dicts with: nombre, apellidos, email, comision, regional.
        """
        ...

@dataclass
class MoodleStudent:
    nombre: str
    apellidos: str
    email: str
    comision: str | None = None
    regional: str | None = None
```

**Mocking strategy:** The client class accepts `base_url` and `token` via constructor. In tests, inject a mock that returns controlled data. The service layer uses the interface `MoodleWSClientProtocol` (Protocol class) for type safety without coupling to the real implementation.

**Error handling:** Connection errors → raise `MoodleConnectionError` → service catches and falls back to manual import suggestion. Auth errors (invalid token) → raise `MoodleAuthError`. Always logged.

### D8 — Moodle WS integration config

Integration details (base_url, token) per tenant stored in configuration. For C-09, the Moodle WS module reads from environment or config:

```python
# Tenant-level config (future: store per tenant in DB)
MOODLE_BASE_URL = settings.MOODLE_BASE_URL
MOODLE_TOKEN = settings.MOODLE_TOKEN
```

For C-09, we use global settings. Per-tenant Moodle config is deferred to a future change when multi-tenant Moodle integration is needed.

### D9 — Vaciar (F1.5, RN-04)

```
POST /api/v1/padron/versiones/{version_id}/vaciar
```

Rules:
1. Load VersionPadron by ID
2. If `version.activa == True` → raise 409 (cannot vaciar active version)
3. Soft-delete all EntradaPadron where `version_id == version_id`
4. Audit log: `PADRON_CARGAR` with accion_note="VACIAR", filas_afectadas=count
5. Return {version_id, entries_vaciadas: count}

**Why only non-active?** Prevents accidental data loss. If you need to replace the padrón, import a new version (which automatically deactivates the old one, then you can vaciar the old one).

### D10 — Schemas

```python
class VersionPadronResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    materia_id: UUID
    cohorte_id: UUID
    cargado_por: UUID
    cargado_at: datetime
    activa: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True, extra='forbid')

class EntradaPadronResponse(BaseModel):
    id: UUID
    version_id: UUID
    tenant_id: UUID
    usuario_id: UUID | None
    nombre: str
    apellidos: str
    email: str  # decrypted
    comision: str | None
    regional: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True, extra='forbid')

class ImportPreviewResponse(BaseModel):
    filename: str
    total_rows: int
    preview_rows: list[dict]
    detected_columns: dict[str, str]  # header → field mapping
    model_config = ConfigDict(extra='forbid')

class ImportConfirmRequest(BaseModel):
    filename: str
    materia_id: UUID
    cohorte_id: UUID
    column_mapping: dict[str, str] | None = None  # override auto-detection
    model_config = ConfigDict(extra='forbid')
```

### D11 — Router structure

| Prefix | Endpoints | Guard | Notes |
|--------|-----------|-------|-------|
| `/api/v1/padron/importar/preview` | POST | `padron:cargar` | Upload file, get preview |
| `/api/v1/padron/importar/confirmar` | POST | `padron:cargar` | Confirm import, create version |
| `/api/v1/padron/versiones` | GET | `padron:ver` | List versions (filter by materia, cohorte) |
| `/api/v1/padron/versiones/{id}` | GET | `padron:ver` | Get version detail |
| `/api/v1/padron/versiones/{id}/entradas` | GET | `padron:ver` | List entries for a version |
| `/api/v1/padron/versiones/{id}/vaciar` | POST | `padron:cargar` | Vaciar entries (F1.5) |

### D12 — Migration 007 structure

```python
# 007_padron_ingesta_moodle.py
# Creates:
#   - version_padron (id UUID PK, tenant_id FK, materia_id FK, cohorte_id FK,
#     cargado_por UUID FK → usuario, cargado_at DateTime, activa Boolean default True,
#     created_at, updated_at, deleted_at)
#   - entrada_padron (id UUID PK, version_id FK → version_padron, tenant_id FK,
#     usuario_id FK → usuario nullable, nombre String, apellidos String, email Text encrypted,
#     comision String nullable, regional String nullable, created_at, updated_at, deleted_at)
# Indexes:
#   - UNIQUE partial: (tenant_id, materia_id, cohorte_id) WHERE activa AND deleted_at IS NULL
#   - FK: version_padron(tenant_id, materia_id) → materia(id)
#   - FK: version_padron(tenant_id, cohorte_id) → cohorte(id)
#   - FK: version_padron(tenant_id, cargado_por) → usuario(id)
#   - FK: entrada_padron(version_id) → version_padron(id)
#   - FK: entrada_padron(tenant_id, usuario_id) → usuario(id)
```

### D13 — File parser design

```python
# backend/app/services/file_parser.py
from dataclasses import dataclass, field

@dataclass
class ParsedRow:
    nombre: str
    apellidos: str
    email: str
    comision: str | None = None
    regional: str | None = None

@dataclass
class ParseResult:
    total_rows: int
    rows: list[ParsedRow]
    detected_columns: dict[str, str]
    errors: list[str] = field(default_factory=list)  # parse warnings

class FileParser:
    def parse(self, file_path: str, encoding: str = "utf-8") -> ParseResult:
        """Parse .xlsx or .csv file into structured rows."""
        ...

    def parse_bytes(self, content: bytes, filename: str) -> ParseResult:
        """Parse file content from bytes (for HTTP upload)."""
        ...
```

Libraries: `openpyxl` for .xlsx, Python `csv` module for .csv. Add `openpyxl` to `requirements.txt` if not present.

### D14 — No service-layer email encrypt/decrypt

Unlike Usuario PII (C-07 D2, service-layer encrypt), EntradaPadron email uses the **EncryptedString TypeDecorator** at the ORM level. This means:
- On write: SQLAlchemy transparently encrypts before INSERT
- On read: SQLAlchemy transparently decrypts after SELECT
- The service and repository layers work with plain text email
- No special encrypt/decrypt methods needed in PadronService

## Risks / Trade-offs

- **[File re-upload on confirm]** → Preview and confirm are separate requests. The file must be re-uploaded for confirm (or stored temporarily). We choose re-upload for simplicity (no temp state). Acceptable for typical file sizes (<5MB). If files grow large, implement temp file storage with TTL.
- **[Single PadronRepository instead of two]** → If VersionPadron and EntradaPadron evolve independently later (e.g., EntradaPadron grows its own domain logic), splitting is a simple refactor.
- **[Moodle WS global config vs per-tenant]** → Using global settings for C-09. Per-tenant Moodle config requires DB storage and admin UI — deferred.
- **[EncryptedString for email vs service-layer encrypt]** → The TypeDecorator approach is simpler but means raw SQL queries won't encrypt/decrypt automatically. For repository-pattern access, this is fine. If raw SQL reporting is needed later, the report layer must handle encryption.
- **[No email uniqueness constraint]** → Unlike Usuario.email (unique per tenant), EntradaPadron.email is NOT unique. Multiple entries can have the same email (same student re-imported in different versions, or a student in multiple comisiones).

## Migration Plan

1. Implement VersionPadron model in `models/padron.py`
2. Implement EntradaPadron model in same file
3. Implement Pydantic schemas in `schemas/padron.py`
4. Implement PadronRepository in `repositories/padron_repository.py`
5. Implement FileParser in `services/file_parser.py`
6. Implement MoodleWSClient in `integrations/moodle_ws.py`
7. Implement PadronService in `services/padron_service.py` (import flow + vaciar)
8. Implement padron router in `api/v1/routers/padron.py` + register in main.py
9. Generate Alembic migration 007
10. Run full test suite (TDD per task)
