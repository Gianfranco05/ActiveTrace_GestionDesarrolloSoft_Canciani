import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.rbac import router as rbac_router
from app.core.dependencies import (
    UserSession,
    get_current_user,
    get_db,
)
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(rbac_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_admin(db_session, tenant) -> Rol:
    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo="usuarios:gestionar")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso)

    rp = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    await db_session.commit()
    return rol


def _admin_session(tenant) -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        roles=["ADMIN"],
    )


def _unauthorized_session(tenant) -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        roles=["ALUMNO"],
    )


@pytest.mark.asyncio
async def test_list_roles(http_client, test_app, db_session, tenant):
    await _seed_admin(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.get("/api/v1/rbac/roles")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["nombre"] == "ADMIN"


@pytest.mark.asyncio
async def test_create_role(http_client, test_app, db_session, tenant):
    await _seed_admin(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.post(
        "/api/v1/rbac/roles",
        json={"nombre": "NUEVO_ROL", "descripcion": "Test role"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["nombre"] == "NUEVO_ROL"
    assert data["descripcion"] == "Test role"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_role_409(http_client, test_app, db_session, tenant):
    await _seed_admin(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    await http_client.post(
        "/api/v1/rbac/roles",
        json={"nombre": "DUPLICADO"},
    )
    resp = await http_client.post(
        "/api/v1/rbac/roles",
        json={"nombre": "DUPLICADO"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_role_with_permisos(http_client, test_app, db_session, tenant):
    await _seed_admin(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.get("/api/v1/rbac/roles")
    assert resp.status_code == 200
    roles = resp.json()
    rol_id = roles[0]["id"]

    resp = await http_client.get(f"/api/v1/rbac/roles/{rol_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nombre"] == "ADMIN"
    assert "permisos" in data
    assert "usuarios:gestionar" in data["permisos"]


@pytest.mark.asyncio
async def test_set_role_permisos(http_client, test_app, db_session, tenant):
    await _seed_admin(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.get("/api/v1/rbac/roles")
    rol_id = resp.json()[0]["id"]

    permiso = Permiso(codigo="otro:permiso")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(permiso)

    resp = await http_client.put(
        f"/api/v1/rbac/roles/{rol_id}/permisos",
        json={"permiso_ids": [str(permiso.id)]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "otro:permiso" in data["permisos"]
    assert "usuarios:gestionar" not in data["permisos"]


@pytest.mark.asyncio
async def test_list_permisos(http_client, test_app, db_session, tenant):
    await _seed_admin(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.get("/api/v1/rbac/permisos")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    codigos = [p["codigo"] for p in data]
    assert "usuarios:gestionar" in codigos


@pytest.mark.asyncio
async def test_create_permiso(http_client, test_app, db_session, tenant):
    await _seed_admin(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.post(
        "/api/v1/rbac/permisos",
        json={"codigo": "nuevo:permiso", "descripcion": "New perm"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["codigo"] == "nuevo:permiso"


@pytest.mark.asyncio
async def test_rbac_without_permission_returns_403(
    http_client, test_app, db_session, tenant,
):
    test_app.dependency_overrides[get_current_user] = lambda: _unauthorized_session(
        tenant,
    )

    resp = await http_client.get("/api/v1/rbac/roles")
    assert resp.status_code == 403
