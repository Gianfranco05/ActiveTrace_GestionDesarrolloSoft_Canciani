import uuid
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.auth_user import RefreshToken, ResetToken
from app.models.auth_user import AuthUser


@pytest.mark.asyncio
async def test_create_refresh_token(db_session, tenant):
    user = AuthUser(
        tenant_id=tenant.id,
        email="refresh_user@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = RefreshToken(
        token_hash="a" * 64,
        user_id=user.id,
        tenant_id=tenant.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(token)
    await db_session.commit()
    await db_session.refresh(token)

    assert isinstance(token.id, uuid.UUID)
    assert token.token_hash == "a" * 64
    assert token.user_id == user.id
    assert token.tenant_id == tenant.id
    assert token.is_used is False
    assert token.expires_at is not None


@pytest.mark.asyncio
async def test_create_reset_token(db_session, tenant):
    user = AuthUser(
        tenant_id=tenant.id,
        email="reset_user@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = ResetToken(
        user_id=user.id,
        token_hash="b" * 64,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(token)
    await db_session.commit()
    await db_session.refresh(token)

    assert isinstance(token.id, uuid.UUID)
    assert token.token_hash == "b" * 64
    assert token.user_id == user.id
    assert token.is_used is False
    assert token.expires_at is not None


@pytest.mark.asyncio
async def test_refresh_token_unique_hash(db_session, tenant):
    user = AuthUser(
        tenant_id=tenant.id,
        email="refresh_unique@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    expires = datetime.now(timezone.utc) + timedelta(days=7)
    t1 = RefreshToken(
        token_hash="unique_hash", user_id=user.id, tenant_id=tenant.id, expires_at=expires,
    )
    db_session.add(t1)
    await db_session.commit()

    t2 = RefreshToken(
        token_hash="unique_hash", user_id=user.id, tenant_id=tenant.id, expires_at=expires,
    )
    db_session.add(t2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_refresh_token_expires_at_required(db_session, tenant):
    user = AuthUser(
        tenant_id=tenant.id,
        email="refresh_expires@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = RefreshToken(
        token_hash="c" * 64,
        user_id=user.id,
        tenant_id=tenant.id,
    )
    db_session.add(token)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_reset_token_expires_at_required(db_session, tenant):
    user = AuthUser(
        tenant_id=tenant.id,
        email="reset_expires@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = ResetToken(
        user_id=user.id,
        token_hash="d" * 64,
    )
    db_session.add(token)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
