"""Smoke test: verifica que el router de tareas está registrado."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.core.config import Settings


@pytest.mark.asyncio
async def test_tareas_router_registered():
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )
    app = create_app(settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/tareas")
        assert resp.status_code == 401
