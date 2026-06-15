"""TDD: Smoke test for encuentros and guardias routers registration."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def smoke_app():
    from app.main import create_app
    return create_app()


@pytest.fixture
def smoke_client(smoke_app):
    transport = ASGITransport(app=smoke_app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_routers_registered_encuentros_slots(smoke_client):
    response = await smoke_client.get("/api/encuentros/slots")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_routers_registered_guardias(smoke_client):
    response = await smoke_client.get("/api/guardias")
    assert response.status_code == 401
