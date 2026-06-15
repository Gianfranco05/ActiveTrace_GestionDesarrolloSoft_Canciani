## Context

C-01 provided the FastAPI skeleton with `core/security.py` reserved for JWT and Argon2 (C-02 only filled AES-256 encryption). C-02 built the tenant foundation: Tenant model, BaseModelMixin, BaseRepository with mandatory tenant scope, and Alembic migration 001. C-03 (this change, governance **CRITICO**) builds the complete authentication layer on top.

Every downstream change (C-04 RBAC, C-05 audit, C-06+ domain entities, C-07 usuarios, C-21 frontend) depends on this change being complete — it provides `get_current_user`, the dependency that resolves identity + tenant from the verified JWT.

The design follows ADR-001 (auth propio, not Moodle SSO), ADR-002 (row-level multi-tenancy), and the project's regla de oro: identity comes exclusively from the session, never from request parameters.

## Goals / Non-Goals

**Goals:**
- AuthUser minimal model for credentials only (scope: auth, not domain User)
- JWT access token (15min) + refresh token (7 days) with rotation
- Login with email + password (Argon2id) + optional TOTP gate
- Refresh rotation with compromise detection (reuse invalidates all tokens)
- 2FA TOTP enrollment and verification via `pyotp`
- Password recovery with one-time token (forgot + reset)
- In-memory rate limiting (5/60s per IP+email)
- `get_current_user` FastAPI dependency resolving identity + tenant from JWT
- Alembic migration 002 (auth_user + refresh_token tables)

**Non-Goals:**
- Full User model with PII (CUIT, DNI, CBU, phone, address) → C-07
- RBAC, permission matrix, `require_permission` guard → C-04
- Audit logging of auth actions (login, 2FA, password change) → C-05
- Real email sending for password recovery → placeholder in C-03, real in C-12
- External rate limiting (Redis) → in-memory is sufficient for C-03; Redis can be added later
- Moodle SSO integration → postponed to Fase 2 per ADR-001

## Decisions

### D1 — AuthUser model: minimal credentials entity

AuthUser represents the authentication identity only — not the full user profile. Fields:

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK, default uuid4 |
| `tenant_id` | UUID | FK → Tenant(id), NOT NULL, indexed |
| `email` | String(255) | NOT NULL, unique per tenant |
| `password_hash` | String(255) | Argon2id hash, NOT NULL |
| `is_2fa_enabled` | Boolean | default False |
| `otp_secret` | String(255) | AES-256-GCM encrypted, nullable |
| `is_active` | Boolean | default True |
| `created_at` | DateTime | auto via BaseModelMixin |
| `updated_at` | DateTime | auto via BaseModelMixin |

Constraints:
- `UNIQUE(tenant_id, email)` — unique email per tenant
- Partial index: `WHERE deleted_at IS NULL` on (tenant_id, email) to allow soft-delete round-trips

Extends `BaseModelMixin` from C-02 (inherits `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`).

**Alternativa descartada**: Single User model with all fields. Descarta porque separar auth identity de perfil PII permite que C-07 evolucione el perfil sin tocar el módulo de auth, y mantiene el principio de mínima exposición de PII.

### D2 — JWT tokens: access + refresh

**Access token:**
- Algorithm: HS256 using `SECRET_KEY` from Settings
- Expiry: 15 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- Claims: `sub` (user_id UUID as string), `tenant_id` (UUID as string), `roles` (list of strings, empty for C-03), `exp` (timestamp), `iat` (timestamp)
- Permissions are NOT stored in the JWT — resolved server-side per request (C-04)

**Refresh token:**
- Opaque random string (64 bytes hex-encoded, via `secrets.token_hex(64)`)
- Stored in `refresh_token` table as SHA-256 hash
- Expiry: 7 days (`REFRESH_TOKEN_EXPIRE_DAYS`)
- Unique ID per token (UUID) for rotation tracking

JWT creation and verification goes in `core/security.py` alongside the existing AES-256 functions.

### D3 — Refresh rotation with compromise detection

RefreshToken table:

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK |
| `token_hash` | String(128) | SHA-256 of opaque token, unique, indexed |
| `user_id` | UUID | FK → AuthUser(id), NOT NULL |
| `tenant_id` | UUID | FK → Tenant(id), NOT NULL |
| `expires_at` | DateTime | NOT NULL |
| `is_used` | Boolean | default False — marks rotated tokens |
| `created_at` | DateTime | auto |

Rotation algorithm:
1. Validate refresh token (hash lookup → match → not expired → not used)
2. Mark old token as `is_used = True`
3. Issue new access + refresh pair
4. Store new refresh token hash

Compromise detection:
- If a refresh token with `is_used = True` is presented again → COMPROMISED
- Set ALL refresh tokens for that user to `is_used = True` (invalidate all sessions)
- Log the event (logging, not audit — audit is C-05)

**Alternativa descartada**: Storing plain refresh tokens in DB. Se descarta porque SHA-256 hashing means even if DB is leaked, refresh tokens cannot be used to impersonate users.

### D4 — Login flow

```
POST /api/auth/login
Body: { email, password }

1. CHECK rate_limiter.is_allowed(ip, email)          ← before any DB operation
2. LOOKUP AuthUser by email + tenant (from domain?)
   NOTE: tenant is NOT known at login time — user enters email only.
   Tenant is resolved from AuthUser record (tenant_id on the user).
3. IF user not found OR not active → return generic 401
4. VERIFY password with Argon2id
5. IF user has is_2fa_enabled:
   → Return { "requires_2fa": true, "session_token": <temp_token> }
6. ELSE:
   → Issue access token + refresh token
   → Return { "access_token", "refresh_token", "token_type": "bearer" }

POST /api/auth/2fa/verify-login
Body: { session_token, totp_code }

1. Validate temp session token (short-lived, stored in memory or signed)
2. Verify TOTP against user's otp_secret
3. Issue real access + refresh tokens
```

The temp session token in step 5 is a short-lived (5min) signed token containing user_id and a flag `2fa_pending: true`. Client sends this back with the TOTP code to complete login.

**Regla de oro**: tenant is resolved from AuthUser record (step 2), NOT from any request parameter. The JWT is then issued with that tenant_id. From that point forward, identity + tenant come exclusively from the verified JWT.

### D5 — 2FA TOTP

- Library: `pyotp` (standard TOTP implementation)
- Secret: 16 bytes base32-encoded (`pyotp.random_base32()`), encrypted with AES-256 and stored in `otp_secret`
- QR URI: `otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}` — returned to client for authenticator app setup

Endpoints:

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/2fa/enroll` | Generates secret, returns `{ secret_base32, qr_uri }` (requires auth, stores temp secret until verified) |
| `POST /api/auth/2fa/verify` | Verifies first TOTP code against temp secret, if valid → encrypts secret, saves to AuthUser, enables 2FA |
| `POST /api/auth/2fa/verify-login` | Part of login flow (see D4) — verifies TOTP after credential check |
| `POST /api/auth/2fa/disable` | Removes 2FA secret, sets `is_2fa_enabled = False` (requires password confirmation) |

Enrollment stores the secret in a temp state (in-memory or separate column) until first verification. This prevents users from locking themselves out by entering an unreadable secret.

### D6 — Password recovery

```
POST /api/auth/forgot
Body: { email }
1. Validate email format
2. Look up AuthUser by email (across all tenants — email is globally unique in practice)
3. If found:
   a. Generate one-time reset token (`secrets.token_urlsafe(48)`)
   b. Store SHA-256 hash of token in `reset_token` table with user_id, expires_at (30min)
   c. LOG the reset token URL (placeholder — real email in C-12):
      `logger.info(f"Reset link for {email}: /auth/reset?token={token}")`
4. Always return 200 (even if email not found — prevents email enumeration)

POST /api/auth/reset
Body: { token, new_password }
1. Hash token, look up in reset_token table
2. If not found OR expired → 400 "Invalid or expired token"
3. Validate new_password strength (min 8 chars, at least 1 uppercase, 1 number)
4. Hash new password with Argon2id
5. Update AuthUser.password_hash
6. Invalidate ALL refresh tokens for that user (force re-login)
7. Delete the reset_token record
```

ResetToken table:
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK |
| `user_id` | UUID | FK → AuthUser(id), NOT NULL |
| `token_hash` | String(128) | SHA-256 of reset token, unique, indexed |
| `expires_at` | DateTime | NOT NULL, default now + 30min |
| `is_used` | Boolean | default False |
| `created_at` | DateTime | auto |

### D7 — Rate limiting

In-memory, dict-based rate limiter:

```python
class RateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
        self._store: dict[str, list[float]] = {}  # key -> [timestamps]

    def is_allowed(self, ip: str, email: str) -> bool:
        key = f"{ip}:{email}"
        now = time.time()
        timestamps = self._store.get(key, [])
        # Remove timestamps outside the window
        timestamps = [t for t in timestamps if now - t < self.window_seconds]
        self._store[key] = timestamps
        if len(timestamps) >= self.max_attempts:
            return False
        timestamps.append(now)
        return True
```

- Key: `"{ip}:{email}"` — scoped to both IP and email
- Window slinding (not fixed): timestamps older than 60s are pruned
- Called BEFORE credential validation in login flow (D4, step 1)
- Returns `429 Too Many Requests` if blocked
- Periodic cleanup to prevent unbounded memory growth (or inline pruning on each check)

**Alternativa descartada**: Redis-based rate limiting. Se descarta porque Redis no está en la arquitectura de C-03; se agregaría como mejora de performance si es necesario. El limiter in-memory es suficiente para el alcance de MVP.

### D8 — get_current_user dependency

FastAPI dependency in `core/dependencies.py`:

```python
async def get_current_user(request: Request) -> UserSession:
    """
    Extracts and verifies JWT from Authorization header.
    Resolves user_id + tenant_id + roles from verified token.
    Injects into request.state and returns UserSession dataclass.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.removeprefix("Bearer ")
    try:
        payload = verify_access_token(token)  # verifies signature + expiry
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_session = UserSession(
        user_id=UUID(payload["sub"]),
        tenant_id=UUID(payload["tenant_id"]),
        roles=payload.get("roles", []),
    )
    request.state.user = user_session
    return user_session
```

`UserSession` is a Pydantic dataclass or simple dataclass: `{ user_id: UUID, tenant_id: UUID, roles: list[str] }`.

This dependency is the foundation for C-04's `require_permission` guard. It does NOT resolve permissions — only identity + roles. Permissions are resolved server-side in C-04.

## Risks / Trade-offs

- **[Rate limiter in-memory no persiste entre restarts]** → Al reiniciar el servidor, el contador de rate limit se pierde. Esto es aceptable porque el window es de solo 60s; un atacante no gana nada del restart. Mitigación: documentado en el código. Si se necesita persistencia, migrar a Redis en C-12+.
- **[Separación AuthUser vs User (C-07) puede crear confusión]** → Es deliberado: el modelo de auth no debe acoplarse al modelo de dominio. C-07 creará un `User` que referencia a `AuthUser.user_id` con una relación 1:1. Mitigación: documentar claramente en ambos modelos que `AuthUser` es solo para credenciales y `User` para perfil.
- **[Temp session token en 2FA gate es stateful en el servidor]** → Para evitar estado, se usa un signed JWT corto (5min) con claim `2fa_pending: true`. El cliente lo envía de vuelta para completar el login. Esto es stateless del lado del servidor.
- **[Password recovery sin email real]** → El placeholder de log no es útil para usuarios reales. Se marca explícitamente como temporal. La integración con email real es C-12 (comunicaciones). Mitigación: tests de integración verifican que el token se genera y persiste correctamente.

## Migration Plan

1. Implement AuthUser model + RefreshToken model + ResetToken model
2. Implement Argon2id hash/verify in `core/security.py`
3. Implement JWT create/verify in `core/security.py`
4. Implement rate limiter in `core/rate_limiter.py`
5. Implement auth repository (BaseRepository for AuthUser, RefreshToken, ResetToken)
6. Implement auth service (login, refresh, logout, forgot, reset)
7. Implement 2FA service (enroll, verify, disable, verify-login)
8. Implement auth router (`/api/auth/*` endpoints)
9. Implement 2FA router (`/api/auth/2fa/*` endpoints)
10. Implement `get_current_user` dependency in `core/dependencies.py`
11. Write all schemas in `schemas/auth.py`
12. Generate Alembic migration 002
13. Write tests per spec (TDD: RED → GREEN → TRIANGULATE for each task)
14. Run full test suite against real PostgreSQL
15. Verify lint + type-check

Rollback: `alembic downgrade -1` removes auth_user, refresh_token, and reset_token tables. All other code (models, services, routers) is new and has no state beyond the DB.

## Open Questions

- **¿Debe el rate limiter resetear en login exitoso?** Decisión: sí — una vez que el usuario ingresa credenciales válidas, el contador de IP+email se resetea a 0. Esto evita que un atacante que robe el password pueda bloquear al usuario legítimo.
- **¿Temp session token para 2FA debe incluir los claims de roles?** Decisión: no — el temp token solo contiene `user_id` + `2fa_pending: true`. Los roles y tenant se emiten en el JWT real después de completar el 2FA.
- **¿Logout debe invalidar solo el refresh token específico o todos los del usuario?** Decisión: solo el refresh token presentado (por ID). Para invalidar todas las sesiones, el usuario debe cambiar su contraseña (que invalida todos los refresh tokens).
