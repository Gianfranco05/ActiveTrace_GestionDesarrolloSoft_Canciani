import uuid

import pytest
from fastapi import FastAPI, status
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


@pytest.mark.asyncio
async def test_full_rbac_flow(http_client, test_app, db_session, tenant):
    u_session = UserSession(
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        roles=["ADMIN"],
    )
    test_app.dependency_overrides[get_current_user] = lambda: u_session

    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    p1 = Permiso(codigo="usuarios:gestionar")
    db_session.add(p1)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(p1)

    rp = RolPermiso(rol_id=rol.id, permiso_id=p1.id)
    db_session.add(rp)
    await db_session.commit()

    rol_resp = await http_client.post(
        "/api/v1/rbac/roles",
        json={"nombre": "TEST_ROLE", "descripcion": "Temp role for integration test"},
    )
    assert rol_resp.status_code == status.HTTP_201_CREATED

    catalog_resp = await http_client.get("/api/v1/rbac/permisos")
    assert catalog_resp.status_code == status.HTTP_200_OK
    catalog = catalog_resp.json()
    assert len(catalog) == 1  # only usuarios:gestionar seeded here

    estado_academico = Permiso(codigo="estado_academico:ver")
    db_session.add(estado_academico)
    await db_session.commit()
    await db_session.refresh(estado_academico)

    assign_resp = await http_client.put(
        f"/api/v1/rbac/roles/{rol_resp.json()['id']}/permisos",
        json={"permiso_ids": [str(estado_academico.id), str(p1.id)]},
    )
    assert assign_resp.status_code == status.HTTP_200_OK

    get_resp = await http_client.get(
        f"/api/v1/rbac/roles/{rol_resp.json()['id']}",
    )
    assert get_resp.status_code == status.HTTP_200_OK
    role_data = get_resp.json()
    assert "estado_academico:ver" in role_data["permisos"]
    assert "usuarios:gestionar" in role_data["permisos"]


@pytest.mark.asyncio
async def test_create_role_inherits_no_permisos(
    http_client, test_app, db_session, tenant,
):
    u_session = UserSession(
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        roles=["ADMIN"],
    )
    test_app.dependency_overrides[get_current_user] = lambda: u_session

    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    p1 = Permiso(codigo="usuarios:gestionar")
    db_session.add(p1)
    await db_session.commit()

    rp = RolPermiso(rol_id=rol.id, permiso_id=p1.id)
    db_session.add(rp)
    await db_session.commit()

    resp = await http_client.post(
        "/api/v1/rbac/roles",
        json={"nombre": "NEW_ROLE"},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    rol_id = resp.json()["id"]

    get_resp = await http_client.get(f"/api/v1/rbac/roles/{rol_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["permisos"] == []
