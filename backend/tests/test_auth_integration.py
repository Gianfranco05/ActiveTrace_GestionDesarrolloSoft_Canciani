import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.rate_limiter import RateLimiter
from app.core.security import hash_password
from app.main import create_app
from app.models.auth_user import AuthUser, ResetToken
from app.repositories.auth_repository import (
    AuthRepository,
    RefreshTokenRepository,
    ResetTokenRepository,
)
from app.services.auth_service import AuthService


@pytest.fixture
def app(db_session: AsyncSession) -> FastAPI:
    application = create_app()

    async def _get_db_override():
        yield db_session

    application.dependency_overrides[get_db] = _get_db_override
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def auth_service(db_session: AsyncSession, tenant) -> AuthService:
    auth_repo = AuthRepository(db_session, tenant.id)
    refresh_repo = RefreshTokenRepository(db_session, tenant.id)
    reset_repo = ResetTokenRepository(db_session, tenant.id)
    return AuthService(
        session=db_session,
        auth_repo=auth_repo,
        refresh_repo=refresh_repo,
        reset_repo=reset_repo,
        rate_limiter=RateLimiter(),
    )


# 17.1 — Multi-tenant isolation
@pytest.mark.asyncio
async def test_login_tenant_a_cannot_access_tenant_b(
    client: AsyncClient, db_session: AsyncSession, tenant,
):
    tenant_b_id = uuid.uuid4()
    from app.models.tenant import Tenant

    tenant_b = Tenant(id=tenant_b_id, name="Tenant C", slug="tenant-c-alt")
    db_session.add(tenant_b)
    await db_session.commit()

    user_a = AuthUser(
        tenant_id=tenant.id,
        email="cross_a@test.com",
        password_hash=hash_password("Secure123"),
    )
    user_b = AuthUser(
        tenant_id=tenant_b_id,
        email="cross_b@test.com",
        password_hash=hash_password("Secure123"),
    )
    db_session.add_all([user_a, user_b])
    await db_session.commit()

    resp = await client.post("/api/auth/login", json={
        "email": "cross_a@test.com",
        "password": "Secure123",
    })
    assert resp.status_code == 200
    token_a = resp.json()["access_token"]

    # Verify token is for tenant A (not tenant B)
    from app.core.security import verify_access_token
    payload = verify_access_token(token_a)
    assert payload["tenant_id"] == str(tenant.id)
    assert payload["tenant_id"] != str(tenant_b_id)


# 17.2 — Token compromise flow
@pytest.mark.asyncio
async def test_token_compromise_flow(
    client: AsyncClient, db_session: AsyncSession, tenant, auth_service,
):
    user = AuthUser(
        tenant_id=tenant.id,
        email="compromise@test.com",
        password_hash=hash_password("Secure123"),
    )
    db_session.add(user)
    await db_session.commit()

    login = await auth_service.login(
        email="compromise@test.com",
        password="Secure123",
        ip="10.0.0.1",
    )
    old_refresh = login["refresh_token"]

    rotate = await auth_service.refresh(old_refresh)
    new_refresh = rotate["refresh_token"]

    with pytest.raises(Exception):
        await auth_service.refresh(old_refresh)

    with pytest.raises(Exception):
        await auth_service.refresh(new_refresh)

    re_login = await auth_service.login(
        email="compromise@test.com",
        password="Secure123",
        ip="10.0.0.1",
    )
    assert "access_token" in re_login


# 17.3 — Rate limit end-to-end through the router
@pytest.mark.asyncio
async def test_rate_limit_end_to_end(
    client: AsyncClient, db_session: AsyncSession, tenant,
):
    user = AuthUser(
        tenant_id=tenant.id,
        email="ratelimit_e2e@test.com",
        password_hash=hash_password("Secure123"),
    )
    db_session.add(user)
    await db_session.commit()

    # Use wrong password to build up rate limit counter
    for i in range(5):
        resp = await client.post(
            "/api/auth/login",
            json={"email": "ratelimit_e2e@test.com", "password": "WrongPass1"},
            headers={"X-Forwarded-For": "10.0.0.99"},
        )
        assert resp.status_code == 401, f"Attempt {i + 1} unexpected: {resp.status_code}"

    resp = await client.post(
        "/api/auth/login",
        json={"email": "ratelimit_e2e@test.com", "password": "WrongPass1"},
        headers={"X-Forwarded-For": "10.0.0.99"},
    )
    assert resp.status_code == 429, f"Expected 429, got {resp.status_code}: {resp.text}"


# 17.4 — Password reset flow
@pytest.mark.asyncio
async def test_password_reset_flow(
    client: AsyncClient, db_session: AsyncSession, tenant, auth_service,
):
    user = AuthUser(
        tenant_id=tenant.id,
        email="fullreset@test.com",
        password_hash=hash_password("OldPass123"),
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/api/auth/forgot", json={
        "email": "fullreset@test.com",
    })
    assert resp.status_code == 200

    raw_token = "integration-test-reset-token"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    reset_model = ResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(reset_model)
    await db_session.commit()

    result = await auth_service.reset_password(raw_token, "NewPass456")
    assert result["message"] == "Password has been reset successfully"

    with pytest.raises(Exception):
        await auth_service.login(
            email="fullreset@test.com",
            password="OldPass123",
            ip="10.0.0.1",
        )

    new_login = await auth_service.login(
        email="fullreset@test.com",
        password="NewPass456",
        ip="10.0.0.1",
    )
    assert isinstance(new_login, dict)
    assert "access_token" in new_login
