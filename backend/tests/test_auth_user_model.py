import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.auth_user import AuthUser


@pytest.fixture
def make_auth_user():
    async def _make(
        db_session,
        tenant,
        email="user@test.com",
        password_hash="$argon2id$hash",
        **kwargs,
    ):
        user = AuthUser(
            tenant_id=tenant.id,
            email=email,
            password_hash=password_hash,
            **kwargs,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _make


@pytest.mark.asyncio
async def test_create_auth_user(db_session, tenant, make_auth_user):
    user = await make_auth_user(
        db_session, tenant, email="create_test@test.com",
    )
    user = AuthUser(
        tenant_id=tenant.id,
        email="user@test.com",
        password_hash="$argon2id$hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.tenant_id == tenant.id
    assert user.email == "user@test.com"
    assert user.password_hash == "$argon2id$hash"
    assert user.is_2fa_enabled is False
    assert user.otp_secret is None
    assert user.is_active is True
    assert user.deleted_at is None


@pytest.mark.asyncio
async def test_auth_user_email_unique_per_tenant(db_session, tenant, make_auth_user):
    await make_auth_user(db_session, tenant, email="same@test.com")

    user2 = AuthUser(
        tenant_id=tenant.id,
        email="same@test.com",
        password_hash="hash2",
    )
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_same_email_different_tenant_allowed(db_session, tenant_a, tenant_b, make_auth_user):
    user_a = await make_auth_user(db_session, tenant_a, email="shared@test.com")

    user_b = AuthUser(
        tenant_id=tenant_b.id,
        email="shared@test.com",
        password_hash="hash2",
    )
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_b)

    assert user_b.id != user_a.id
    assert user_b.email == "shared@test.com"


@pytest.mark.asyncio
async def test_auth_user_requires_tenant_id(db_session):
    user = AuthUser(
        email="notenant@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_auth_user_is_active_default_true(db_session, tenant, make_auth_user):
    user = await make_auth_user(
        db_session, tenant, email="active_default@test.com",
    )

    assert user.is_active is True
