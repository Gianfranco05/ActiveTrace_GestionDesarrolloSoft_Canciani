## Why

activia-trace requires secure authentication before any user can access the system. C-01 set up the infrastructure, C-02 built the tenant foundation — but without auth there is no way to identify users, resolve their tenant, or protect endpoints. This change delivers the complete authentication layer: email+password login with Argon2id, JWT access tokens with refresh rotation, optional TOTP 2FA, password recovery, rate limiting, and the `get_current_user` dependency that every protected endpoint downstream depends on.

This is governance CRITICO — it is the identity backbone of the system.

## What Changes

- **AuthUser model** — minimal user entity for credentials only (id, tenant_id, email unique per tenant, password_hash Argon2id, is_2fa_enabled, otp_secret encrypted nullable, is_active, timestamps). Full User with PII comes in C-07.
- **JWT tokens** — access token (15min) with `sub`, `tenant_id`, `roles`, `exp` claims. Refresh token (7 days, opaque, stored hashed with rotation).
- **Refresh rotation** — each refresh has a unique ID; on use, old is invalidated and new pair issued. Reuse of already-used refresh token invalidates ALL tokens for that user (compromise detection).
- **Login endpoint** — `POST /api/auth/login` validates credentials → checks 2FA gate → issues tokens.
- **2FA TOTP** — optional per user: enroll (`POST /api/auth/2fa/enroll` returns QR URI), verify (`POST /api/auth/2fa/verify` enables), login gate (`POST /api/auth/2fa/verify-login`). Uses `pyotp`.
- **Token refresh & logout** — `POST /api/auth/refresh` rotates, `POST /api/auth/logout` revokes refresh.
- **Password recovery** — `POST /api/auth/forgot` generates one-time reset token (short expiry, stored hashed) + `POST /api/auth/reset` sets new password. Email sending is placeholder (real email in C-12).
- **Rate limiting** — 5 attempts / 60s per IP+email combo during login. In-memory dict (no Redis needed for C-03).
- **get_current_user dependency** — FastAPI dependency that verifies JWT from Authorization header, resolves user_id + tenant_id + roles, injects into `request.state`.
- **Alembic migration 002** — creates `auth_user` and `refresh_token` tables.

## Capabilities

### New Capabilities

- `auth-user`: AuthUser model with email+password credentials, 2FA flags, Argon2id hashing
- `jwt-tokens`: Access and refresh token creation, verification, and lifecycle management
- `login-and-2fa`: Login flow with credential validation, optional TOTP gate, and session issuance
- `password-recovery`: Forgot password (one-time token) and reset password flow
- `rate-limiting`: In-memory rate limiter — 5 attempts per 60s per IP+email combination
- `auth-dependencies`: FastAPI dependencies `get_current_user` and `get_tenant` that resolve identity from verified JWT

### Modified Capabilities

- *(none — all capabilities are new)*

## Impact

- **Models**: `backend/app/models/auth_user.py` — AuthUser + RefreshToken ORM models
- **Core**: `backend/app/core/security.py` — ADD JWT create/verify, Argon2id hash/verify (C-02 had AES-256 only)
- **Core**: `backend/app/core/dependencies.py` — ADD `get_current_user`, `get_tenant`; keep existing `get_db`
- **Core**: `backend/app/core/rate_limiter.py` — NEW in-memory rate limiter
- **Routers**: `backend/app/api/v1/routers/auth.py` — Login, refresh, logout, forgot, reset endpoints
- **Routers**: `backend/app/api/v1/routers/2fa.py` — 2FA enrollment and verification endpoints
- **Schemas**: `backend/app/schemas/auth.py` — Request/response Pydantic schemas for all auth flows
- **Services**: `backend/app/services/auth_service.py` — Auth business logic
- **Services**: `backend/app/services/2fa_service.py` — 2FA business logic
- **Services**: `backend/app/services/rate_limiter_service.py` — Rate limiter logic
- **Repositories**: `backend/app/repositories/auth_repository.py` — AuthUser + RefreshToken queries
- **Dependencies**: `pyotp` — for TOTP 2FA generation and verification
- **Migration**: `backend/alembic/versions/002_auth_user.py` — creates auth_user, refresh_token tables
