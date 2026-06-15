from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_user import AuthUser, RefreshToken, ResetToken
from app.repositories.auth_repository import (
    AuthRepository,
    RefreshTokenRepository,
    ResetTokenRepository,
)


@pytest.fixture
def auth_repo(db_session: AsyncSession, tenant) -> AuthRepository:
    return AuthRepository(db_session, tenant.id)


@pytest.fixture
def refresh_repo(db_session: AsyncSession, tenant) -> RefreshTokenRepository:
    return RefreshTokenRepository(db_session, tenant.id)


@pytest.fixture
def reset_repo(db_session: AsyncSession, tenant) -> ResetTokenRepository:
    return ResetTokenRepository(db_session, tenant.id)


@pytest.mark.asyncio
async def test_find_by_email(
    db_session: AsyncSession, auth_repo: AuthRepository, tenant,
):
    user = AuthUser(
        tenant_id=tenant.id,
        email="find_me@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()

    found = await auth_repo.find_by_email("find_me@test.com")
    assert found is not None
    assert found.email == "find_me@test.com"
    assert found.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_find_by_email_returns_none_for_wrong_tenant(
    db_session: AsyncSession, auth_repo: AuthRepository, tenant_a, tenant_b,
):
    user = AuthUser(
        tenant_id=tenant_a.id,
        email="cross_tenant@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()

    repo_b = AuthRepository(db_session, tenant_b.id)
    found = await repo_b.find_by_email("cross_tenant@test.com")
    assert found is None


@pytest.mark.asyncio
async def test_find_by_email_across_tenants(
    db_session: AsyncSession, auth_repo: AuthRepository, tenant,
):
    user = AuthUser(
        tenant_id=tenant.id,
        email="across_tenants@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()

    found = await auth_repo.find_by_email_across_tenants("across_tenants@test.com")
    assert found is not None
    assert found.email == "across_tenants@test.com"


@pytest.mark.asyncio
async def test_find_by_email_across_tenants_nonexistent(
    db_session: AsyncSession, auth_repo: AuthRepository,
):
    found = await auth_repo.find_by_email_across_tenants("nobody@test.com")
    assert found is None


@pytest.mark.asyncio
async def test_refresh_find_by_hash(
    db_session: AsyncSession, refresh_repo: RefreshTokenRepository, tenant,
):
    user = AuthUser(
        tenant_id=tenant.id, email="refresh_hash@test.com", password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = RefreshToken(
        token_hash="abc123hash",
        user_id=user.id,
        tenant_id=tenant.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(token)
    await db_session.commit()

    found = await refresh_repo.find_by_hash("abc123hash")
    assert found is not None
    assert found.token_hash == "abc123hash"
    assert found.user_id == user.id


@pytest.mark.asyncio
async def test_refresh_find_by_hash_nonexistent(
    refresh_repo: RefreshTokenRepository,
):
    found = await refresh_repo.find_by_hash("nonexistent")
    assert found is None


@pytest.mark.asyncio
async def test_invalidate_all_for_user(
    db_session: AsyncSession, refresh_repo: RefreshTokenRepository, tenant,
):
    user = AuthUser(
        tenant_id=tenant.id, email="invalidate_all@test.com", password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    expires = datetime.now(timezone.utc) + timedelta(days=7)
    for i in range(3):
        t = RefreshToken(
            token_hash=f"hash_{i}",
            user_id=user.id,
            tenant_id=tenant.id,
            expires_at=expires,
        )
        db_session.add(t)
    await db_session.commit()

    await refresh_repo.invalidate_all_for_user(user.id)

    for i in range(3):
        found = await refresh_repo.find_by_hash(f"hash_{i}")
        assert found is not None
        assert found.is_used is True


@pytest.mark.asyncio
async def test_reset_find_by_hash(
    db_session: AsyncSession, reset_repo: ResetTokenRepository, tenant,
):
    user = AuthUser(
        tenant_id=tenant.id, email="reset_find@test.com", password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = ResetToken(
        token_hash="reset_hash_123",
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(token)
    await db_session.commit()

    found = await reset_repo.find_by_hash("reset_hash_123")
    assert found is not None
    assert found.token_hash == "reset_hash_123"


@pytest.mark.asyncio
async def test_reset_mark_used(
    db_session: AsyncSession, reset_repo: ResetTokenRepository, tenant,
):
    user = AuthUser(
        tenant_id=tenant.id, email="reset_mark@test.com", password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = ResetToken(
        token_hash="mark_used_hash",
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(token)
    await db_session.commit()
    await db_session.refresh(token)

    await reset_repo.mark_used(token.id)

    found = await reset_repo.find_by_hash("mark_used_hash")
    assert found is not None
    assert found.is_used is True
