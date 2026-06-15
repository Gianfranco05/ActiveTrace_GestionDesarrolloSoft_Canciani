## 1. AuthUser Model — RED → GREEN → TRIANGULATE

- [x] 1.1 RED: Write failing test `test_auth_user_model.py` — `test_create_auth_user` expects UUID id, tenant_id, email, password_hash, is_2fa_enabled=False, otp_secret=None, is_active=True
- [x] 1.2 GREEN: Implement `backend/app/models/auth_user.py` — AuthUser ORM with fields per D1, extends BaseModelMixin
- [x] 1.3 Execute tests: confirm GREEN
- [x] 1.4 TRIANGULATE: Add `test_auth_user_email_unique_per_tenant` (duplicate email same tenant → IntegrityError), `test_same_email_different_tenant_allowed`, `test_auth_user_requires_tenant_id`, `test_auth_user_is_active_default_true`
- [x] 1.5 Execute tests: confirm all pass
- [x] 1.6 REFACTOR: Extract AuthUser factory fixture, ensure BaseModelMixin compatibility

## 2. Argon2id Password Hashing — RED → GREEN → TRIANGULATE

- [x] 2.1 RED: Write failing test `test_password_hashing.py` — `test_hash_and_verify` expects `verify_password(plaintext, hash_password(plaintext)) == True`
- [x] 2.2 GREEN: Implement `hash_password(plaintext: str) -> str` and `verify_password(plaintext: str, hashed: str) -> bool` using Argon2id in `core/security.py`
- [x] 2.3 Execute tests: confirm GREEN
- [x] 2.4 TRIANGULATE: Add `test_wrong_password_fails_verify`, `test_same_password_different_hashes`
- [x] 2.5 Execute tests: confirm all pass
- [x] 2.6 REFACTOR: Extract Argon2id password helper class, handle Argon2Error gracefully

## 3. RefreshToken and ResetToken Models — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test `test_auth_token_models.py` — `test_create_refresh_token` expects UUID id, token_hash, user_id, tenant_id, expires_at, is_used=False
- [x] 3.2 GREEN: Implement `RefreshToken` model referencing AuthUser — fields per D3
- [x] 3.3 GREEN: Implement `ResetToken` model referencing AuthUser — fields per D6
- [x] 3.4 Execute tests: confirm GREEN
- [x] 3.5 TRIANGULATE: Add `test_refresh_token_expires_at_required`, `test_reset_token_expires_at_default_30min`
- [x] 3.6 Execute tests: confirm all pass

## 4. JWT Access Token — RED → GREEN → TRIANGULATE

- [x] 4.1 RED: Write failing test `test_jwt_tokens.py` — `test_create_access_token` expects a valid JWT string that can be decoded with correct sub, tenant_id, roles, exp, iat claims
- [x] 4.2 GREEN: Implement `create_access_token(user_id, tenant_id, roles, expires_delta)` in `core/security.py` using `python-jose` with HS256
- [x] 4.3 GREEN: Implement `verify_access_token(token)` that returns payload dict or raises `JWTError`
- [x] 4.4 Execute tests: confirm GREEN
- [x] 4.5 TRIANGULATE: Add `test_access_token_expires` (sleep past expiry → raises), `test_tampered_token_rejected` (modify payload → fails), `test_access_token_claims_match_input`
- [x] 4.6 Execute tests: confirm all pass
- [x] 4.7 REFACTOR: Extract token constants, ensure SECRET_KEY from Settings

## 5. Refresh Token Creation and Rotation — RED → GREEN → TRIANGULATE

- [x] 5.1 RED: Write failing test `test_refresh_token_rotation.py` — `test_create_refresh_token` expects opaque string + stored hash in DB
- [x] 5.2 GREEN: Implement `create_refresh_token(session, user_id, tenant_id)` in auth service — generates opaque token, stores SHA-256 hash in RefreshToken table
- [x] 5.3 Execute tests: confirm GREEN
- [x] 5.4 RED: Write failing test `test_rotate_refresh_token` — old token marked used, new pair issued
- [x] 5.5 GREEN: Implement `rotate_refresh_token(session, old_token)` — validate hash, mark used, issue new pair
- [x] 5.6 Execute tests: confirm GREEN
- [x] 5.7 TRIANGULATE: Add `test_used_refresh_rejected`, `test_expired_refresh_rejected`, `test_nonexistent_refresh_rejected`, `test_compromise_detection` (reuse of rotated token invalidates all user tokens)
- [x] 5.8 Execute tests: confirm all pass
- [x] 5.9 REFACTOR: Extract token hash utility, ensure no plaintext token in DB logs

## 6. Rate Limiter — RED → GREEN → TRIANGULATE

- [x] 6.1 RED: Write failing test `test_rate_limiter.py` — `test_allow_within_limit` expects 5 attempts allowed in 60s window
- [x] 6.2 GREEN: Implement `RateLimiter` class in `core/rate_limiter.py` — dict-based, max_attempts=5, window_seconds=60, key=f"{ip}:{email}"
- [x] 6.3 Execute tests: confirm GREEN
- [x] 6.4 TRIANGULATE: Add `test_block_exceeds_limit` (6th attempt blocked), `test_window_slides` (wait 60s → allowed), `test_different_ip_same_email_independent`, `test_same_ip_different_email_independent`, `test_reset_on_success`, `test_expired_entries_cleaned`
- [x] 6.5 Execute tests: confirm all pass
- [x] 6.6 REFACTOR: Make RateLimiter configurable, ensure thread-safety (or document single-threaded assumption)

## 7. Auth Schemas — Implementation

- [x] 7.1 Implement `schemas/auth.py` — `LoginRequest(email, password)`, `LoginResponse(access_token, refresh_token, token_type)`, `Login2FARequiredResponse(requires_2fa, session_token)`, `RefreshRequest(refresh_token)`, `RefreshResponse(access_token, refresh_token, token_type)`, `LogoutRequest(refresh_token)`, `ForgotRequest(email)`, `ResetRequest(token, new_password)`, `Enroll2FAResponse(secret_base32, qr_uri)`, `Verify2FARequest(totp_code)`, `VerifyLogin2FARequest(session_token, totp_code)`, `Disable2FARequest(password)`

- [x] 7.2 All schemas use `model_config = ConfigDict(extra='forbid')`

## 8. Auth Repository — RED → GREEN → TRIANGULATE

- [x] 8.1 RED: Write failing test `test_auth_repository.py` — `test_find_by_email` expects AuthUser lookup by (email, tenant_id)
- [x] 8.2 GREEN: Implement `AuthRepository(BaseRepository[AuthUser])` — `find_by_email(email)`, `find_by_email_across_tenants(email)` (for forgot password)
- [x] 8.3 GREEN: Implement `RefreshTokenRepository(BaseRepository[RefreshToken])` — `find_by_hash(token_hash)`, `invalidate_all_for_user(user_id)`
- [x] 8.4 GREEN: Implement `ResetTokenRepository(BaseRepository[ResetToken])` — `find_by_hash(token_hash)`, `mark_used(token_id)`
- [x] 8.5 Execute tests: confirm all GREEN
- [x] 8.6 TRIANGULATE: Add `test_find_by_email_returns_none_for_wrong_tenant`, `test_invalidate_all_for_user_updates_all`
- [x] 8.7 Execute tests: confirm all pass

## 9. Auth Service — RED → GREEN → TRIANGULATE

- [x] 9.1 RED: Write failing test `test_auth_service_login.py` — `test_login_success` expects access + refresh tokens on valid credentials
- [x] 9.2 GREEN: Implement `AuthService` — `login(email, password, ip)` with rate limiter check → user lookup → password verify → 2FA gate check → token issuance
- [x] 9.3 Execute tests: confirm GREEN
- [x] 9.4 TRIANGULATE: Add `test_login_wrong_password`, `test_login_nonexistent_email`, `test_login_inactive_user`, `test_login_with_2fa_requires_second_factor`, `test_login_rate_limited_returns_429`
- [x] 9.5 Execute tests: confirm all pass
- [x] 9.6 REFACTOR: Ensure tenant_id passed through service chain correctly

## 10. Refresh and Logout — RED → GREEN → TRIANGULATE

- [x] 10.1 RED: Write failing test `test_auth_service_refresh.py` — `test_refresh_success` expects new token pair
- [x] 10.2 GREEN: Implement `refresh(refresh_token)` in AuthService
- [x] 10.3 Execute tests: confirm GREEN
- [x] 10.4 TRIANGULATE: Add `test_refresh_used_token`, `test_refresh_expired`, `test_refresh_compromise_detection`
- [x] 10.5 GREEN: Implement `logout(refresh_token)` in AuthService
- [x] 10.6 Execute tests: confirm GREEN for logout scenarios
- [x] 10.7 REFACTOR: Share token validation logic between refresh and logout

## 11. 2FA TOTP Service — RED → GREEN → TRIANGULATE

- [x] 11.1 RED: Write failing test `test_2fa_service.py` — `test_enroll_generates_secret` expects base32 secret + QR URI
- [x] 11.2 GREEN: Implement `TwoFAService` — `enroll(user_id)` generates pyotp secret, stores temp, returns secret + QR URI
- [x] 11.3 Execute tests: confirm GREEN
- [x] 11.4 RED: Write failing test `test_verify_totp_enables_2fa` — verifies code against temp secret, sets is_2fa_enabled=True
- [x] 11.5 GREEN: Implement `verify(user_id, totp_code)` — verifies and persists encrypted secret
- [x] 11.6 Execute tests: confirm GREEN
- [x] 11.7 TRIANGULATE: Add `test_verify_login_totp_gate` (valid TOTP after login → tokens), `test_verify_login_invalid_totp`, `test_verify_login_expired_session_token`, `test_disable_2fa_with_password`, `test_disable_2fa_wrong_password`
- [x] 11.8 Execute tests: confirm all pass

## 12. Password Recovery Service — RED → GREEN → TRIANGULATE

- [x] 12.1 RED: Write failing test `test_password_recovery.py` — `test_forgot_password_creates_token` expects reset token persisted for existing email
- [x] 12.2 GREEN: Implement `forgot_password(email)` in AuthService — generates token, stores hash, logs URL (placeholder)
- [x] 12.3 Execute tests: confirm GREEN
- [x] 12.4 RED: Write failing test `test_reset_password_updates_hash` — valid token sets new password
- [x] 12.5 GREEN: Implement `reset_password(token, new_password)` — validate token, hash new password, update, invalidate all refresh tokens
- [x] 12.6 Execute tests: confirm GREEN
- [x] 12.7 TRIANGULATE: Add `test_forgot_nonexistent_email_returns_200` (no enumeration), `test_reset_expired_token`, `test_reset_used_token`, `test_reset_weak_password`, `test_reset_invalidates_all_sessions`
- [x] 12.8 Execute tests: confirm all pass

## 13. Auth Router — RED → GREEN → TRIANGULATE

- [x] 13.1 RED: Write failing integration test `test_auth_router.py` — `test_login_endpoint` POST /api/auth/login returns tokens
- [x] 13.2 GREEN: Implement `backend/app/api/v1/routers/auth.py` — POST /api/auth/login, POST /api/auth/refresh, POST /api/auth/logout, POST /api/auth/forgot, POST /api/auth/reset
- [x] 13.3 Execute tests: confirm GREEN
- [x] 13.4 TRIANGULATE: Add integration tests for all login variants, refresh, logout, forgot, reset endpoints
- [x] 13.5 Execute tests: confirm all pass

## 14. 2FA Router — RED → GREEN → TRIANGULATE

- [x] 14.1 RED: Write failing test `test_2fa_router.py` — `test_enroll_endpoint` POST /api/auth/2fa/enroll (authenticated) returns secret + QR
- [x] 14.2 GREEN: Implement `backend/app/api/v1/routers/2fa.py` — POST /api/auth/2fa/enroll, POST /api/auth/2fa/verify, POST /api/auth/2fa/verify-login, POST /api/auth/2fa/disable
- [x] 14.3 Execute tests: confirm GREEN
- [x] 14.4 TRIANGULATE: Add integration tests for full 2FA lifecycle: enroll → verify → login → verify-login → disable
- [x] 14.5 Execute tests: confirm all pass

## 15. get_current_user Dependency — RED → GREEN → TRIANGULATE

- [x] 15.1 RED: Write failing test `test_dependencies.py` — `test_get_current_user_valid_token` returns UserSession
- [x] 15.2 GREEN: Implement `get_current_user` in `core/dependencies.py` — extract Bearer token, verify, return UserSession, set request.state.user
- [x] 15.3 GREEN: Implement `get_tenant` dependency extracting tenant_id from UserSession
- [x] 15.4 GREEN: Define `UserSession` dataclass in `core/dependencies.py`
- [x] 15.5 Execute tests: confirm GREEN
- [x] 15.6 TRIANGULATE: Add `test_get_current_user_no_header`, `test_get_current_user_non_bearer`, `test_get_current_user_expired`, `test_get_current_user_tampered`
- [x] 15.7 Execute tests: confirm all pass

## 16. Alembic Migration 002

- [x] 16.1 Generate migration: `002_auth_user.py` — creates auth_user, refresh_token, reset_token tables
- [x] 16.2 Verify partial unique index `ix_auth_user_email_active` on (tenant_id, email) WHERE deleted_at IS NULL
- [x] 16.3 Update `backend/app/models/__init__.py` — export AuthUser, RefreshToken, ResetToken
- [~] 16.4 Execute migration: `alembic upgrade head` against dev DB (pending — requires PostgreSQL)
- [~] 16.5 Test rollback: `alembic downgrade -1` (pending — requires PostgreSQL)

## 17. Integration and Isolation Tests

- [x] 17.1 Write `test_auth_multi_tenant.py` — multi-tenant isolation via token claims
- [x] 17.2 Write `test_token_compromise_flow.py` — full scenario: rotate → reuse old → all tokens invalidated
- [x] 17.3 Write `test_rate_limit_end_to_end.py` — 6 rapid login attempts → 429 on 6th
- [x] 17.4 Write `test_password_reset_flow.py` — forgot → reset → old password fails → new password works
- [x] 17.5 Execute full test suite: 109 tests all pass
- [~] 17.6 Verify test coverage ≥80% lines for new code (pending — no coverage tool configured)

## 18. Documentation and Cleanup

- [x] 18.1 Update docstrings in `core/security.py` marking `# C-03: JWT/Argon2` sections
- [x] 18.2 Remove any `# reserved for C-03` markers from C-02 code (none found)
- [x] 18.3 Run linting/type-checking on all new files — ruff: all checks passed
