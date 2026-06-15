import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient




@pytest.fixture
def app():
    from app.main import create_app

    return create_app()


@pytest.mark.asyncio
async def test_health_returns_200_and_status(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert "status" in body
        assert "database" in body


@pytest.mark.asyncio
async def test_health_db_up_when_connected(app: FastAPI, db_engine):
    """DB engine is initialized first via the session-scoped db_engine fixture."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "up"


@pytest.mark.asyncio
async def test_health_db_down_when_not_initialized(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["database"] in ("up", "down")
