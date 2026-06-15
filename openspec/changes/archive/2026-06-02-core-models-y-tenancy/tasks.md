## 1. Tenant Model — RED → GREEN → TRIANGULATE

- [x] 1.1 RED: Write failing test `test_tenant_model.py` — `test_create_tenant` expects UUID id, name, slug, is_active defaults
- [x] 1.2 GREEN: Implement `backend/app/models/tenant.py` — Tenant ORM with UUID PK, name (unique), slug (unique, indexed), is_active (default True)
- [x] 1.3 Execute tests: confirm GREEN (tenant test passes)
- [x] 1.4 TRIANGULATE: Add `test_tenant_slug_uniqueness` (duplicate slug raises IntegrityError), `test_tenant_name_uniqueness` (duplicate name raises IntegrityError)
- [x] 1.5 Execute tests: confirm all pass (generalize if Fake It breaks)
- [x] 1.6 REFACTOR: Extract tenant factory/conftest fixture, clean up test setup

## 2. Base Mixin with Soft Delete — RED → GREEN → TRIANGULATE

- [x] 2.1 RED: Write failing test `test_base_mixin.py` — `test_mixin_has_uuid` expects auto-generated UUID on new entity
- [x] 2.2 GREEN: Implement `backend/app/models/base.py` — `BaseModelMixin` with `id` (UUID, PK, default uuid4), `tenant_id` (UUID, FK → Tenant, NOT NULL, indexed), `created_at`, `updated_at` (auto timestamps), `deleted_at` (nullable, soft delete)
- [x] 2.3 Execute tests: confirm GREEN
- [x] 2.4 TRIANGULATE: Add `test_mixin_tenant_id_required` (missing tenant_id → IntegrityError), `test_mixin_timestamps_auto_populate` (created_at set on insert, updated_at changes on update), `test_mixin_deleted_at_null_by_default`, `test_mixin_soft_delete_marks_timestamp`
- [x] 2.5 Execute tests: confirm all pass
- [x] 2.6 REFACTOR: Ensure BaseModelMixin is `DeclarativeBase`-compatible, clean up fixture for temp entity

## 3. Generic Repository with Tenant Scope — RED → GREEN → TRIANGULATE

- [x] 3.1 RED: Write failing test `test_base_repository.py` — `test_repo_scope_list` expects `BaseRepository(tenant_id=A).list()` returns only Tenant A records
- [x] 3.2 GREEN: Implement `backend/app/repositories/base.py` — `BaseRepository[T]` generic async repo with `__init__(session, tenant_id)`, `list()`, `get()`, `create()`, `update()`, `soft_delete()`, applying `WHERE tenant_id = :tid AND deleted_at IS NULL` by default
- [x] 3.3 Execute tests: confirm GREEN
- [x] 3.4 TRIANGULATE: Add `test_repo_create_sets_tenant_id`, `test_repo_get_filters_tenant`, `test_repo_update_scoped`, `test_repo_soft_delete_excludes`, `test_repo_with_deleted_includes`, `test_repo_only_deleted_returns_deleted`, `test_repo_cross_tenant_isolation` (Tenant A cannot see Tenant B data)
- [x] 3.5 Execute tests: confirm all pass
- [x] 3.6 REFACTOR: Extract query builder, ensure type safety with `TypeVar('T', bound=BaseModelMixin)`, clean up fixtures

## 4. AES-256 Encryption Utilities — RED → GREEN → TRIANGULATE

- [x] 4.1 RED: Write failing test `test_encryption.py` — `test_encrypt_decrypt_roundtrip` expects `decrypt(encrypt(plaintext)) == plaintext`
- [x] 4.2 GREEN: Implement AES-256-GCM `encrypt()` / `decrypt()` in `backend/app/core/security.py` using `cryptography` library, with `ENCRYPTION_KEY` from Settings
- [x] 4.3 Execute tests: confirm GREEN
- [x] 4.4 TRIANGULATE: Add `test_encrypt_different_nonce` (same plaintext → different ciphertext), `test_decrypt_invalid_ciphertext_raises` (tampered data → `EncryptionError`), `test_encrypt_or_none` (None in → None out), `test_decrypt_or_none` (None in → None out), `test_encrypt_logs_nothing` (plaintext not in log output)
- [x] 4.5 Execute tests: confirm all pass
- [x] 4.6 REFACTOR: Extract `EncryptionError` to `core/exceptions.py`, ensure key derivation uses HKDF or direct bytes

## 5. Fill tenancy.py with Tenant Resolution

- [x] 5.1 Implement `backend/app/core/tenancy.py` — `get_tenant_id_from_request(request) -> uuid.UUID` that reads tenant_id from request.state (to be set by C-03 auth middleware)
- [x] 5.2 Implement `backend/app/core/dependencies.py` — dependency `get_tenant_id` that extracts tenant_id for endpoint injection
- [x] 5.3 Write test `test_tenancy.py` — `test_get_tenant_id_with_override` (dependency override in test returns correct tenant_id)
- [x] 5.4 Execute tests: confirm pass

## 6. Alembic Migration 001

- [x] 6.1 Configure `backend/alembic/env.py` for async engine using `run_async()` with asyncpg driver
- [x] 6.2 Generate migration 001: `alembic revision --autogenerate -m "initial_tenant"` — creates `tenant` table
- [x] 6.3 Add seed data: default tenant with `slug = "default"` and `name = "Default Tenant"` in migration's `upgrade()` (removed in `downgrade()`)
- [x] 6.4 Update `backend/app/models/__init__.py` — export `BaseModelMixin` from `base.py` and `Tenant` from `tenant.py`
- [x] 6.5 Execute migration: `alembic upgrade head` against dev DB, verify table exists
- [x] 6.6 Test rollback: `alembic downgrade -1`, verify table removed

## 7. Integration and Isolation Tests

- [x] 7.1 Write `test_multi_tenant_isolation.py` — create two tenants, insert records for each, verify repository for Tenant A does not return Tenant B records (get, list, update scope)
- [x] 7.2 Write `test_soft_delete_lifecycle.py` — create → soft_delete → list excludes → with_deleted includes → only_deleted returns
- [x] 7.3 Write `test_encryption_round_trip.py` — encrypt all PII-like fields (DNI, CUIL, CBU, email), decrypt, verify round-trip integrity
- [x] 7.4 Write `test_mixin_timestamps.py` — create entity → verify created_at and updated_at are set; update → verify updated_at changes
- [x] 7.5 Execute full test suite: all tests pass against real PostgreSQL
- [x] 7.6 Verify test coverage ≥80% lines for new code

## 8. Documentation and Cleanup

- [x] 8.1 Update docstrings in `core/security.py` marking `# C-02: AES-256` sections and `# C-03: JWT/Argon2 (reserved)`
- [x] 8.2 Update docstrings in `core/tenancy.py` noting dependency on C-03 auth middleware
- [x] 8.3 Run linting/type-checking on all new files
