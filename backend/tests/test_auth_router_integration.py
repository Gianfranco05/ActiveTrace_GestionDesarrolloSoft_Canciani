import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import hash_password
from app.models.auth_user import AuthUser
from app.main import create_app


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


@pytest.mark.asyncio
async def test_health_still_works(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_login_endpoint_returns_tokens(
    client: AsyncClient, db_session: AsyncSession, tenant,
):
    user = AuthUser(
        tenant_id=tenant.id,
        email="router_login@test.com",
        password_hash=hash_password("Secure123"),
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/api/auth/login", json={
        "email": "router_login@test.com",
        "password": "Secure123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(
    client: AsyncClient, db_session: AsyncSession, tenant,
):
    user = AuthUser(
        tenant_id=tenant.id,
        email="router_wrong@test.com",
        password_hash=hash_password("Secure123"),
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/api/auth/login", json={
        "email": "router_wrong@test.com",
        "password": "WrongPass1",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email_returns_401(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={
        "email": "nobody@test.com",
        "password": "SomePass1",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_forgot_endpoint_returns_200(
    client: AsyncClient, db_session: AsyncSession, tenant,
):
    user = AuthUser(
        tenant_id=tenant.id,
        email="router_forgot@test.com",
        password_hash=hash_password("Secure123"),
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/api/auth/forgot", json={
        "email": "router_forgot@test.com",
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_forgot_nonexistent_returns_200(client: AsyncClient):
    resp = await client.post("/api/auth/forgot", json={
        "email": "nobody@test.com",
    })
    assert resp.status_code == 200
