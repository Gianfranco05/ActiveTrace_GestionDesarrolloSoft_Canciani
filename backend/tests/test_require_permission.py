import uuid

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import (
    UserSession,
    get_current_user,
    get_db,
    require_permission,
)
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso


@pytest.fixture
def test_app(db_session):
    app = FastAPI()

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _setup_admin_role(db_session, tenant, user_id):
    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo="test:access")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso)

    rp = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    await db_session.commit()

    return rol, permiso


@pytest.mark.asyncio
async def test_user_with_permission_passes(
    http_client, test_app, db_session, tenant,
):
    rol, permiso = await _setup_admin_role(db_session, tenant, uuid.uuid4())

    def _override_user():
        return UserSession(
            user_id=uuid.uuid4(),
            tenant_id=tenant.id,
            roles=["ADMIN"],
        )

    test_app.dependency_overrides[get_current_user] = _override_user

    called = False

    @test_app.get("/test-pass")
    async def test_endpoint(
        _=Depends(require_permission("test:access")),
    ):
        nonlocal called
        called = True
        return {"ok": True}

    resp = await http_client.get("/test-pass")
    assert resp.status_code == 200
    assert called is True


@pytest.mark.asyncio
async def test_user_without_permission_gets_403(
    http_client, test_app, db_session, tenant,
):
    def _override_user():
        return UserSession(
            user_id=uuid.uuid4(),
            tenant_id=tenant.id,
            roles=["ADMIN"],
        )

    test_app.dependency_overrides[get_current_user] = _override_user

    @test_app.get("/test-forbid")
    async def test_endpoint(
        _=Depends(require_permission("nonexistent:perm")),
    ):
        return {"ok": True}

    resp = await http_client.get("/test-forbid")
    assert resp.status_code == 403
    assert resp.json() == {"detail": "Forbidden"}


@pytest.mark.asyncio
async def test_unauthenticated_gets_401_before_403(
    http_client, test_app, db_session,
):
    @test_app.get("/test-unauth")
    async def test_endpoint(
        _=Depends(require_permission("test:access")),
    ):
        return {"ok": True}

    resp = await http_client.get("/test-unauth")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_empty_roles_gets_403(
    http_client, test_app, db_session, tenant,
):
    def _override_user():
        return UserSession(
            user_id=uuid.uuid4(),
            tenant_id=tenant.id,
            roles=[],
        )

    test_app.dependency_overrides[get_current_user] = _override_user

    @test_app.get("/test-empty")
    async def test_endpoint(
        _=Depends(require_permission("test:access")),
    ):
        return {"ok": True}

    resp = await http_client.get("/test-empty")
    assert resp.status_code == 403
    assert resp.json() == {"detail": "Forbidden"}


@pytest.mark.asyncio
async def test_require_permission_returns_user(
    http_client, test_app, db_session, tenant,
):
    from app.core.dependencies import require_permission_return_user

    rol, permiso = await _setup_admin_role(db_session, tenant, uuid.uuid4())

    def _override_user():
        return UserSession(
            user_id=uuid.uuid4(),
            tenant_id=tenant.id,
            roles=["ADMIN"],
        )

    test_app.dependency_overrides[get_current_user] = _override_user

    captured_user = None

    @test_app.get("/test-return-user")
    async def test_endpoint(
        current_user=Depends(require_permission_return_user("test:access")),
    ):
        nonlocal captured_user
        captured_user = current_user
        return {"ok": True}

    resp = await http_client.get("/test-return-user")
    assert resp.status_code == 200
    assert captured_user is not None
    assert captured_user.roles == ["ADMIN"]
