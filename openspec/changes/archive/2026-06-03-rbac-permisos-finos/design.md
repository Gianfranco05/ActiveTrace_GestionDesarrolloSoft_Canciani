## Context

C-03 delivered the authentication layer: JWT access tokens, refresh rotation, 2FA TOTP, and the `get_current_user` dependency that resolves `UserSession(user_id, tenant_id, roles)`. The JWT carries `roles` as a claim (initially empty — C-07 fills these via role assignments).

C-04 (governance **CRITICO**) builds the authorization layer on top. Every downstream change (C-05 audit, C-06+ domain entities, C-07 usuarios, C-21 frontend) depends on `require_permission` being available to protect its endpoints.

The design follows the KB §3 (modelo de autorización) matrix and ADR rules: permissions are server-side only, fail-closed, and the Rol×Permiso matrix is DATA (not hardcoded).

## Goals / Non-Goals

**Goals:**
- Rol, Permiso, and RolPermiso ORM models (all extend BaseModelMixin from C-02)
- Seed all 7 roles (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS)
- Seed all permissions from KB §3.3 matrix (~20) as `modulo:accion` codes
- Seed all role-permission mappings from the matrix
- `require_permission(codigo)` FastAPI guard that returns 403 if the user lacks the permission
- Permission resolution via server-side DB query (not cached in JWT)
- RBAC admin CRUD: list roles/permisos, create/update roles (ADMIN only)
- Alembic migration 003 (rol, permiso, rol_permiso tables + seed data)

**Non-Goals:**
- Role assignment to users (mapping User ↔ Rol) → C-07
- (propio) scoping and context filtering → per-domain service layer in each change (C-07 onwards)
- Impersonation logic (`impersonacion:usar` is SEEDED but the feature is C-05)
- Audit logging of RBAC changes → C-05
- Frontend RBAC admin UI → C-21
- Caching permissions in JWT or Redis → explicit design choice (D1)

## Decisions

### D1 — Permission resolution is SERVER-SIDE only

Permissions are NOT stored in the JWT. The JWT carries only `roles` (list of role name strings). Every protected request does a DB query to resolve effective permissions for the user's roles.

```sql
SELECT DISTINCT p.codigo
FROM permiso p
JOIN rol_permiso rp ON rp.permiso_id = p.id
JOIN rol r ON r.id = rp.rol_id
WHERE r.nombre IN (:role_names)
```

Rationale:
- Permissions change at runtime (an ADMIN can modify the matrix)
- JWT size stays small (roles list, not full permission set)
- Revocation is immediate: change the RolPermiso mapping and the next request reflects it
- No cache invalidation complexity at this stage

**Alternativa descartada**: Embedding permissions in the JWT. Descartada because it would require token re-issuance whenever the matrix changes, making permission management fragile and immediate revocation impossible.

### D2 — roles in JWT are initially empty

C-03 carries `roles` as a claim. C-07 (usuarios-y-asignaciones) is the change that creates the Asignacion model linking User → Rol with temporal validity. Until C-07 is complete, ALL users will have empty roles → ALL `require_permission` checks will return 403. This is **correct behavior** (fail-closed). The system is not usable for domain operations until C-07 assigns roles.

For development/testing, C-04 can include a test helper that creates roles directly on the session for integration tests.

### D3 — Guard signature and behavior

```python
def require_permission(codigo: str):
    """
    FastAPI dependency. Usage:
        @router.get("/endpoint")
        async def my_endpoint(
            _: None = Depends(require_permission("modulo:accion")),
            current_user: UserSession = Depends(get_current_user),
        ):
    """
    async def dependency(
        current_user: UserSession = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        if not current_user.roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        # Query effective permissions for user's roles
        effective = await rbac_repo.get_effective_permissions(
            db, current_user.roles
        )
        
        if codigo not in effective:
            raise HTTPException(status_code=403, detail="Forbidden")
    
    return dependency
```

The guard returns `None` (or the UserSession) — it either passes (allowing the request to proceed) or raises 403. It does NOT modify the request.

A secondary variant `require_permission_return_user(codigo)` can return the UserSession for endpoints that need it without declaring two dependencies.

### D4 — Model design: Rol, Permiso, RolPermiso

All models extend `BaseModelMixin` from C-02 (inherits UUID pk, tenant_id FK, timestamps, soft delete).

**Rol:**
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK, default uuid4 |
| `tenant_id` | UUID | FK → Tenant(id), NOT NULL, indexed |
| `nombre` | String(50) | NOT NULL, unique per tenant |
| `descripcion` | Text | nullable |
| `created_at` | DateTime | auto via BaseModelMixin |
| `updated_at` | DateTime | auto via BaseModelMixin |
| `deleted_at` | DateTime | nullable, soft delete |

Constraints: `UNIQUE(tenant_id, nombre)`, partial index `WHERE deleted_at IS NULL`.

**Permiso:**
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK, default uuid4 |
| `codigo` | String(80) | NOT NULL, format `modulo:accion`, UNIQUE |
| `descripcion` | Text | nullable |
| `created_at` | DateTime | auto via BaseModelMixin |

Permiso is **tenant-agnostic** (shared across tenants, not scoped). The same permission code means the same thing for every tenant. This simplifies the RBAC model — tenants select from a shared catalog of permissions.

**RolPermiso:**
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK, default uuid4 |
| `rol_id` | UUID | FK → Rol(id), NOT NULL |
| `permiso_id` | UUID | FK → Permiso(id), NOT NULL |
| `created_at` | DateTime | auto |

Constraints: `UNIQUE(rol_id, permiso_id)`.

RolPermiso is tenant-scoped via the Rol (which has tenant_id). Joining RolPermiso → Rol enforces the tenant boundary.

### D5 — Seed data: full permission matrix

The matrix from KB §3.3 is seeded in migration 003. This means:
1. INSERT all 7 roles
2. INSERT all permissions (~20)
3. INSERT all RolPermiso mappings (role × permission intersections)

Rol names (seeded): `ALUMNO`, `TUTOR`, `PROFESOR`, `COORDINADOR`, `NEXO`, `ADMIN`, `FINANZAS`

Note: `NEXO` appears in the KB but has ZERO explicit permissions in the KB §3.3 matrix (empty row). The seed should create the role with no permission mappings. NEXO's actual permissions are a business question (PA-25 in knowledge-base/10_preguntas_abiertas.md) and will be resolved later.

Permissions seeded (codigo → description):

| codigo | description |
|--------|-------------|
| `estado_academico:ver` | Ver estado académico propio |
| `evaluacion:reservar` | Reservar instancia de evaluación |
| `aviso:confirmar` | Confirmar avisos (acknowledgment) |
| `calificaciones:importar` | Importar calificaciones |
| `atrasados:ver` | Ver alumnos atrasados |
| `entregas:detectar_sin_corregir` | Detectar entregas sin corregir |
| `comunicacion:enviar` | Enviar comunicaciones a alumnos |
| `comunicacion:aprobar` | Aprobar comunicaciones masivas |
| `encuentros:gestionar` | Gestionar encuentros |
| `guardias:registrar` | Registrar guardias |
| `tareas:gestionar` | Gestionar tareas internas |
| `avisos:publicar` | Publicar avisos |
| `equipos:asignar` | Gestionar equipos docentes |
| `estructura:gestionar` | Gestionar estructura académica |
| `usuarios:gestionar` | Gestionar usuarios del tenant |
| `auditoria:ver` | Ver auditoría |
| `liquidaciones:operar_grilla` | Operar grilla salarial |
| `liquidaciones:calcular_cerrar` | Calcular y cerrar liquidaciones |
| `facturas:gestionar` | Gestionar facturas |
| `tenant:configurar` | Configurar el tenant |
| `impersonacion:usar` | Usar impersonación |

### D6 — Extensible catalog (ADMIN CRUD)

Admin CRUD endpoints for roles and permissions:

| Endpoint | Method | Permission Required | Description |
|----------|--------|---------------------|-------------|
| `/api/v1/rbac/roles` | GET | `usuarios:gestionar` | List all roles (scoped to tenant) |
| `/api/v1/rbac/roles` | POST | `usuarios:gestionar` | Create new role |
| `/api/v1/rbac/roles/{id}` | GET | `usuarios:gestionar` | Get role details with permissions |
| `/api/v1/rbac/roles/{id}` | PUT | `usuarios:gestionar` | Update role |
| `/api/v1/rbac/roles/{id}/permisos` | PUT | `usuarios:gestionar` | Set permissions for a role |
| `/api/v1/rbac/permisos` | GET | `usuarios:gestionar` | List all permissions (global catalog) |
| `/api/v1/rbac/permisos` | POST | `usuarios:gestionar` | Create new permission |

Note: `usuarios:gestionar` is ADMIN-only (from the matrix). In practice, only ADMIN can manage the catalog.

### D7 — (propio) scoping is NOT in C-04

The KB matrix shows some permissions as `(propio)`, meaning the user can act only on their own data (e.g., PROFESOR can import grades only for their own comisiones). This scoping is a RUNTIME check at the service layer in each domain change (C-07 onwards). C-04's `require_permission` only checks IF the user has the permission at all. The context filter is applied by the domain service.

For example:
- C-04 guard: `require_permission("calificaciones:importar")` → passes if the user has this permission
- C-10 service: checks that the PROFESOR is importing grades for their own comision → 403 if not

This separation keeps C-04 clean and prevents coupling the permission system to domain entity logic.

### D8 — NEXO role with empty permission set

The NEXO role is seeded but has NO permission mappings in the KB §3.3 matrix. This is intentional — NEXO's actual permissions are tied to PA-25 (an open question about its scope). The role exists in the catalog so it can be assigned in C-07, but until PA-25 is resolved, NEXO grants no permissions.

## Risks / Trade-offs

- **[Permission resolution per-request is slower than cached]** → Each protected request does a 3-table JOIN. For high-throughput endpoints this could add latency. Mitigation: the query is simple (indexed FK joins, distinct on one column), and Postgres caches query plans. If profiling shows this is a bottleneck, a Redis cache can be added in a later change (C-12+).
- **[Empty roles → all endpoints return 403 until C-07]** → This is intentional (fail-closed). Mitigation: document this explicitly. Developers can test C-04's guard in isolation with integration tests that inject roles directly into the session.
- **[NEXO has no permissions]** → KB PA-25 is unresolved. The role is created to avoid schema changes later, but it grants zero permissions until PA-25 is decided.

## Migration Plan

1. Implement Rol, Permiso, RolPermiso models in `models/`
2. Implement RbacRepository (get_permissions_for_roles, role CRUD, permission CRUD)
3. Implement RbacService (business logic for permission resolution)
4. Implement `require_permission` guard in `core/dependencies.py`
5. Implement RBAC router (`/api/v1/rbac/*`)
6. Implement RBAC schemas
7. Generate Alembic migration 003 with all seed data
8. Write tests per spec (TDD: RED → GREEN → TRIANGULATE for each task)
9. Run full test suite
10. Verify lint + type-check

Rollback: `alembic downgrade -1` removes rol, permiso, and rol_permiso tables. All new code (models, services, routers) is additive and has no state beyond the DB.

## Open Questions

- **¿Debe NEXO tener algún permiso por defecto?** Decisión: no — se crea el rol sin mappings. Se decide al resolver PA-25.
- **¿Los permisos deben ser tenant-agnostic o tenant-scoped?** Decisión: tenant-agnostic (compartidos). Cada tenant selecciona qué permisos asigna a qué roles. Esto simplifica la administración global y evita duplicación.
- **¿Las migraciones de seed deben ser idempotentes?** Sí — usar `INSERT ... ON CONFLICT DO NOTHING` para roles y permisos, y limpiar + re-insertar mappings de RolPermiso para cada tenant seed.
