## Context

C-06 delivered Carrera, Cohorte, Materia with EstadoRegistro. C-04 delivered RBAC with Rol table and seed data. C-03 delivered AuthUser (identity) and JWT issuance. C-02 delivered BaseModelMixin, tenant isolation, and AES-256-GCM encryption.

C-07 builds the **people and authorization bridge** — Usuario (1:1 profile extension of AuthUser) and Asignacion (role-context assignments with temporal vigencia). The critical architectural decision is wiring Asignaciones into the JWT issuance flow so roles are no longer empty.

Governance is **CRITICO** because: (1) PII encryption invariants, (2) auth flow modification (the role resolver bridge), (3) the role resolver is a security boundary — incorrect resolution means incorrect authorization.

## Goals / Non-Goals

**Goals:**
- Usuario ORM model with 1:1 FK to AuthUser, PII encrypted via AES-256-GCM
- Asignacion ORM model with FKs to Usuario, Rol, Materia (nullable), Carrera (nullable), Cohorte (nullable), self-referential responsable_id
- PII safe response schemas (no PII in lists, full PII in detail views)
- RoleResolver service that reads active Asignaciones and resolves distinct rol_ids
- AuthService `_issue_tokens()` enriched with resolved roles (the critical bridge)
- Usuario CRUD endpoints guarded by `usuarios:gestionar`
- Asignacion CRUD endpoints guarded by `equipos:asignar`
- Alembic migration 006 with usuario, asignacion tables
- Soft delete on all models via BaseModelMixin

**Non-Goals:**
- `equipos-docentes` views (mis-equipos, masiva, clonar) — C-08
- Bulk import/export of usuarios — future change
- PII exposure via API even with permission (deferred — MVP returns PII in detail only)
- Frontend UI — C-21 shell covers this later
- `comisiones` validation (no CRUD for comisiones as standalone entity yet)

## Decisions

### D1 — Usuario is 1:1 with AuthUser, NOT merged

AuthUser (C-03) handles identity: email, password_hash, 2FA, is_active. Usuario (C-07) handles profile: nombre, apellidos, PII, legajos, business attributes. They are separate tables with a 1:1 FK (usuario.id → auth_user.id).

**Why not a single table?**
- AuthUser has auth-specific fields (password_hash, otp_secret, is_2fa_enabled) with strict security constraints
- Usuario has business PII with different access patterns (encrypted, safe/full responses)
- Separation minimizes the blast radius of any schema change
- The 1:1 FK is enforced at the DB level — every AuthUser MUST have exactly one Usuario (created atomically during registration)

### D2 — PII Encryption via AES-256-GCM (core/security.py)

Fields `dni`, `cuil`, `cbu`, `alias_cbu` use AES-256-GCM from C-02's `core/security.py`. Implementation:

```python
# In usuario_service.py:
from app.core.security import encrypt_value, decrypt_value

class UsuarioService:
    async def create(self, data: UsuarioCreate) -> UsuarioResponse:
        encrypted = {}
        for pii_field in PII_FIELDS:
            if data[pii_field]:
                encrypted[pii_field] = encrypt_value(data[pii_field])
        data.update(encrypted)
        return await self._repo.create(data)

    async def get_with_pii(self, id: UUID) -> UsuarioResponse:
        entity = await self._repo.get(id)
        for field in PII_FIELDS:
            value = decrypt_value(getattr(entity, field))
            setattr(entity, field, value)
        return entity
```

Rules:
- Encrypt BEFORE storing (repository or service layer)
- Decrypt ONLY on explicit detail read (not in lists)
- PII NEVER appears in log messages, error responses, or list API responses
- PII columns are `Text` type in the DB (encrypted binary as base64 string)

### D3 — Asignacion model with derived vigencia

`estado_vigencia` is NOT a stored column. It's a computed property:

```python
@property
def estado_vigencia(self) -> str:
    today = date.today()
    if self.vig_desde <= today and (self.vig_hasta is None or self.vig_hasta >= today):
        return "Vigente"
    return "Vencida"
```

**Why derived?**
- Avoids stale state (no cron job needed to flip expired assignments)
- Single source of truth: vig_desde/vig_hasta always define the state
- The Rol table from C-04 used `nombre` for role identity; Asignacion references it by FK

### D4 — Unique constraint on Asignacion

```python
UniqueConstraint(
    "usuario_id", "rol_id", "materia_id", "carrera_id", "cohorte_id",
    name="uq_asignacion_context"
)
```

Partial index: `WHERE deleted_at IS NULL`. This prevents duplicate active assignments (same user, same role, same context). Multiple historical assignments for the same context are allowed (each with non-overlapping vigencia).

`vig_desde` is excluded from the unique constraint to keep it simple — the business layer enforces non-overlapping dates in the service.

### D5 — The CRITICAL Bridge: RoleResolver

This is the most important architectural decision in C-07. Currently C-03's `_issue_tokens()` uses `roles=[]`:

```python
access_token = create_access_token(
    user_id=str(user.id),
    tenant_id=str(user.tenant_id),
    roles=[],  # ← EMPTY — must be populated
)
```

**Approach**: Create a `RoleResolver` service that:
1. Accepts an `AuthUser` (or `user_id` + `tenant_id`)
2. Queries `Asignacion` for active records (vig_desde <= today, vig_hasta >= today or NULL, deleted_at IS NULL)
3. Joins through `Rol` to get distinct `rol.nombre` values
4. Returns `list[str]` of role names

```python
class RoleResolver:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def resolve_roles(self, user_id: UUID) -> list[str]:
        """Resolve distinct role names from active Asignaciones."""
        stmt = (
            select(Rol.nombre)
            .distinct()
            .join(Asignacion, Asignacion.rol_id == Rol.id)
            .where(
                Asignacion.usuario_id == user_id,
                Asignacion.tenant_id == self._tenant_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.vig_desde <= date.today(),
                Asignacion.vig_hasta.is_(None) | (Asignacion.vig_hasta >= date.today()),
                Rol.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.fetchall()]
```

**Where it's called:**

1. `AuthService._issue_tokens()` — after login, before issuing JWT
2. `AuthService._create_temp_2fa_token()` — same, for the 2FA pending token

**Dependency injection**: The `AuthService.__init__()` gains an optional `role_resolver: RoleResolver | None = None` parameter. When NOT provided (e.g., tests), roles default to `[]` — backward compatible. C-07's router wiring always provides it.

### D6 — get_current_user enrichment (no structural change)

`get_current_user` in `dependencies.py` already reads `payload.get("roles", [])` from the JWT:

```python
roles=payload.get("roles", []),
```

Since `_issue_tokens()` now embeds resolved roles in the JWT, this just works — no change needed in `dependencies.py` for the roles field itself. However, we add a convenience method `get_current_user_with_permissions()` that also loads the Usuario profile if needed.

### D7 — PII safe response schemas

Two response schemas:

```python
class UsuarioResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    nombre: str
    apellidos: str
    dni: str  # decrypted
    cuil: str  # decrypted
    cbu: str  # decrypted
    alias_cbu: str  # decrypted
    banco: str | None
    regional: str | None
    legajo: str | None
    legajo_profesional: str | None
    facturador: bool
    estado: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True, extra='forbid')

class UsuarioSafeResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    nombre: str
    apellidos: str
    banco: str | None
    regional: str | None
    legajo: str | None
    legajo_profesional: str | None
    facturador: bool
    estado: str
    model_config = ConfigDict(from_attributes=True, extra='forbid')
```

List endpoints return `UsuarioSafeResponse`. Detail endpoints return `UsuarioResponse` (with decrypted PII).

### D8 — Asignacion schemas

```python
class AsignacionCreate(BaseModel):
    usuario_id: UUID
    rol_id: UUID
    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    comisiones: str | None = None  # JSON string or comma-separated
    responsable_id: UUID | None = None
    vig_desde: date
    vig_hasta: date | None = None
    model_config = ConfigDict(extra='forbid')

class AsignacionResponse(BaseModel):
    id: UUID
    usuario_id: UUID
    rol_id: UUID
    materia_id: UUID | None
    carrera_id: UUID | None
    cohorte_id: UUID | None
    comisiones: str | None
    responsable_id: UUID | None
    vig_desde: date
    vig_hasta: date | None
    estado_vigencia: str  # DERIVED — computed by the model
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True, extra='forbid')
```

### D9 — Router structure

| Prefix | Endpoints | Guard |
|--------|-----------|-------|
| `/api/admin/usuarios` | GET /, POST /, GET /{id}, PUT /{id}, DELETE /{id} | `usuarios:gestionar` |
| `/api/asignaciones` | GET /, POST /, GET /{id}, PUT /{id}, DELETE /{id} | `equipos:asignar` |

### D10 — Migration 006 structure

```
# 006_usuarios_y_asignaciones.py
# Creates:
#   - usuario (id UUID PK FK → auth_user.id, tenant_id FK → tenant, nombre, apellidos,
#     dni TEXT, cuil TEXT, cbu TEXT, alias_cbu TEXT, banco, regional, legajo,
#     legajo_profesional, facturador BOOL DEFAULT false, estado VARCHAR(20) DEFAULT "Activo",
#     created_at, updated_at, deleted_at)
#   - asignacion (id UUID PK, tenant_id FK → tenant, usuario_id FK → usuario,
#     rol_id FK → rol, materia_id FK → materia nullable, carrera_id FK → carrera nullable,
#     cohorte_id FK → cohorte nullable, comisiones TEXT nullable,
#     responsable_id FK → asignacion.id nullable, vig_desde DATE, vig_hasta DATE nullable,
#     created_at, updated_at, deleted_at)
# Indexes:
#   - usuario: UNIQUE(tenant_id, id) partial WHERE deleted_at IS NULL
#   - asignacion: UNIQUE(usuario_id, rol_id, materia_id, carrera_id, cohorte_id)
#     partial WHERE deleted_at IS NULL
#   - asignacion: FK(tenant_id, usuario_id) → usuario
#   - asignacion: FK(tenant_id, rol_id) → rol
#   - asignacion: FK(tenant_id, materia_id) → materia
#   - asignacion: FK(tenant_id, carrera_id) → carrera
#   - asignacion: FK(tenant_id, cohorte_id) → cohorte
#   - asignacion: FK(responsable_id) → asignacion.id
```

## Migration Plan

1. Implement Usuario model in `models/usuario.py` + update `models/__init__.py`
2. Implement Asignacion model in `models/asignacion.py` + FK references
3. Implement Usuario schemas in `schemas/usuario.py` (safe + full response)
4. Implement Asignacion schemas in `schemas/asignacion.py`
5. Implement UsuarioRepository in `repositories/usuario_repository.py`
6. Implement AsignacionRepository in `repositories/asignacion_repository.py`
7. Implement RoleResolver service in `services/role_resolver.py`
8. Implement UsuarioService in `services/usuario_service.py` (PII encryption)
9. Implement AsignacionService in `services/asignacion_service.py`
10. Modify `AuthService._issue_tokens()` and `_create_temp_2fa_token()` — inject RoleResolver
11. Implement usuario router in `api/v1/routers/usuarios.py` + register in main.py
12. Implement asignacion router in `api/v1/routers/asignaciones.py` + register in main.py
13. Generate Alembic migration 006
14. Run full test suite (TDD: RED → GREEN → TRIANGULATE per task)

## Risks / Trade-offs

- **[RoleResolver introduces circular dependency fear]** → RoleResolver depends on Asignacion (C-07) and Rol (C-04). AuthService (C-03) calls RoleResolver. Since AuthService already depends on repositories, adding a role resolver parameter is additive — no circular import if wired via DI (the router creates RoleResolver and passes it to AuthService).
- **[PII decryption performance]** → Decrypting PII on every detail read adds latency (~1ms per field). Acceptable for detail views; lists use safe responses (no decryption).
- **[comisiones as TEXT]** → Using TEXT instead of Postgres ARRAY or JSONB keeps it simple for now. If structured querying of comisiones is needed later, migrate to JSONB or a join table.
- **[No overlapping vigencia enforcement in DB]** → The unique constraint doesn't include vig_desde. The service layer enforces non-overlapping dates. Acceptable risk — a DB-level exclusion constraint would be more robust but adds complexity and isn't standard in Alembic autogenerate.

## Open Questions

- **¿AuthUser creation should also create Usuario atomically?** Decision: YES — when a new AuthUser is registered (C-03 flow), a corresponding Usuario row MUST be created. This is handled by the registration endpoint in C-03. C-07 adds a note that the registration flow must be updated. For initial implementation, Usuario is created separately via the admin API.
- **¿Should the 1:1 FK be enforced as a DB constraint or app-level?** Decision: DB constraint. `usuario.id` is a FK to `auth_user.id` with ON DELETE CASCADE. This guarantees consistency even if an admin deletes directly.
- **¿What about the C-03 seed admin user?** The seed admin (created during tenant setup in C-03) needs a corresponding Usuario. We add a data migration or seed script that creates Usuario rows for existing AuthUser rows when migration 006 runs.
