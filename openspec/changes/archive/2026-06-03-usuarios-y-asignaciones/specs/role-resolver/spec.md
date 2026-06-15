## ADDED Requirements

### Requirement: RoleResolver service

The system SHALL provide a RoleResolver service that reads active Asignaciones for a given user and resolves the distinct role names. This is THE CRITICAL BRIDGE between Asignaciones (C-07) and JWT issuance (C-03).

```python
class RoleResolver:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        ...

    async def resolve_roles(self, user_id: uuid.UUID) -> list[str]:
        """
        Resolve distinct Rol.nombre values from active Asignaciones.
        Active = vig_desde <= today AND (vig_hasta IS NULL OR vig_hasta >= today)
                AND deleted_at IS NULL
        """
        ...
```

**Query logic**:
- FROM Rol (C-04)
- JOIN Asignacion ON Asignacion.rol_id = Rol.id
- WHERE Asignacion.usuario_id = user_id
- AND Asignacion.tenant_id = tenant_id
- AND Asignacion.deleted_at IS NULL
- AND Asignacion.vig_desde <= CURRENT_DATE
- AND (Asignacion.vig_hasta IS NULL OR Asignacion.vig_hasta >= CURRENT_DATE)
- AND Rol.deleted_at IS NULL
- SELECT DISTINCT Rol.nombre

#### Scenario: Resolve roles for user with active assignments
- **WHEN** a user has active Asignaciones (vigente) linked to roles
- **THEN** resolve_roles SHALL return a list of distinct role names

#### Scenario: Resolve roles returns empty for user without assignments
- **WHEN** a user has NO Asignaciones
- **THEN** resolve_roles SHALL return an empty list

#### Scenario: Resolve roles excludes expired assignments
- **WHEN** a user has an Asignacion with vig_hasta < today
- **THEN** resolve_roles SHALL NOT include roles from expired assignments

#### Scenario: Resolve roles excludes soft-deleted assignments
- **WHEN** a user has a soft-deleted Asignacion
- **THEN** resolve_roles SHALL NOT include roles from deleted assignments

#### Scenario: Resolve roles excludes soft-deleted roles
- **WHEN** a user has an Asignacion linked to a soft-deleted Rol
- **THEN** resolve_roles SHALL NOT include that role name

#### Scenario: Resolve roles returns distinct names
- **WHEN** a user has multiple Asignaciones linked to the same Rol
- **THEN** the role name SHALL appear only once in the result

### Requirement: AuthService role resolution integration

The `AuthService` SHALL be modified to resolve roles via RoleResolver during token issuance:

**`_issue_tokens(self, user: AuthUser)` modification**:
- AFTER determining user identity, call `role_resolver.resolve_roles(user.id)`
- Pass the resolved roles to `create_access_token()` instead of `roles=[]`
- The `role_resolver` parameter is OPTIONAL in `__init__` — when None, roles default to `[]`

**`_create_temp_2fa_token()` modification**:
- Same pattern — resolve roles and include in the 2FA pending token

**`__init__` signature change**:
```python
def __init__(
    self,
    session: AsyncSession,
    auth_repo: AuthRepository,
    refresh_repo: RefreshTokenRepository,
    reset_repo: ResetTokenRepository,
    rate_limiter: RateLimiter,
    role_resolver: RoleResolver | None = None,  # NEW — optional
):
    ...
    self._role_resolver = role_resolver
```

#### Scenario: AuthService login includes resolved roles
- **WHEN** calling login() and the user has active Asignaciones
- **THEN** the access_token claims SHALL include the resolved roles

#### Scenario: AuthService login with no role_resolver
- **WHEN** calling login() and role_resolver is None
- **THEN** the access_token claims SHALL include roles=[] (backward compatible)

#### Scenario: AuthService refresh includes resolved roles
- **WHEN** calling refresh() and the user has active Asignaciones
- **THEN** the access_token claims SHALL include the resolved roles

### Requirement: get_current_user enrichment

The `get_current_user` dependency in `core/dependencies.py` ALREADY reads `payload.get("roles", [])` from the JWT. Since `_issue_tokens()` now embeds resolved roles, no structural change is needed at the dependency level.

However, the system SHALL add a convenience property on UserSession:

```python
@dataclass
class UserSession:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    roles: list[str] = field(default_factory=list)

    @property
    def has_role(self, role_name: str) -> bool:
        return role_name in self.roles
```

#### Scenario: UserSession.has_role works correctly
- **WHEN** calling has_role("ADMIN") on a UserSession with roles=["ADMIN"]
- **THEN** True SHALL be returned
- **WHEN** calling has_role("ALUMNO") on the same session
- **THEN** False SHALL be returned
