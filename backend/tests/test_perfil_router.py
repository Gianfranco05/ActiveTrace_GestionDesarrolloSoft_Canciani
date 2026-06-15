import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.perfil import router as perfil_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.core.security import encrypt, hash_password
from app.models.auth_user import AuthUser
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.usuario import Usuario


@pytest.fixture
def p_app(db_session):
    app = FastAPI()
    app.include_router(perfil_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def p_client(p_app):
    transport = ASGITransport(app=p_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_perfil_permiso(db_session, tenant):
    rol = Rol(nombre="PROFESOR", tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo="perfil:editar")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso)
    rp = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    await db_session.commit()
    return rol


async def _create_usuario(db_session, tenant, email, nombre, **kwargs):
    auth = AuthUser(
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password("Test1234!"),
    )
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)

    u_data = {"id": auth.id, "tenant_id": tenant.id, "nombre": nombre, "apellidos": "Test", **kwargs}
    u = Usuario(**u_data)
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return auth, u


def _profesor_session(user_id, tenant):
    return UserSession(user_id=user_id, tenant_id=tenant.id, roles=["PROFESOR"])


@pytest.mark.asyncio
async def test_get_perfil_200(p_client, p_app, db_session, tenant):
    await _seed_perfil_permiso(db_session, tenant)
    auth, u = await _create_usuario(
        db_session, tenant, "perfil_router@test.com", "Router",
        dni=encrypt("99887766"), cuil=encrypt("27-99887766-5"),
    )

    p_app.dependency_overrides[get_current_user] = lambda: _profesor_session(auth.id, tenant)
    resp = await p_client.get("/api/perfil")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nombre"] == "Router"
    assert data["email"] == "perfil_router@test.com"
    assert data["dni"] == "99887766"
    assert data["cuil"] == "27-99887766-5"


@pytest.mark.asyncio
async def test_put_perfil_actualiza_nombre(p_client, p_app, db_session, tenant):
    await _seed_perfil_permiso(db_session, tenant)
    auth, u = await _create_usuario(db_session, tenant, "put_nombre@test.com", "Old")

    p_app.dependency_overrides[get_current_user] = lambda: _profesor_session(auth.id, tenant)
    resp = await p_client.put("/api/perfil", json={"nombre": "NuevoNombre"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["nombre"] == "NuevoNombre"


@pytest.mark.asyncio
async def test_put_perfil_rechaza_cuil(p_client, p_app, db_session, tenant):
    await _seed_perfil_permiso(db_session, tenant)
    auth, u = await _create_usuario(db_session, tenant, "put_cuil@test.com", "User")

    p_app.dependency_overrides[get_current_user] = lambda: _profesor_session(auth.id, tenant)
    resp = await p_client.put("/api/perfil", json={"cuil": "20-12345678-9"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_put_perfil_parcial(p_client, p_app, db_session, tenant):
    await _seed_perfil_permiso(db_session, tenant)
    auth, u = await _create_usuario(db_session, tenant, "put_partial@test.com", "Nombre", regional="CABA")

    p_app.dependency_overrides[get_current_user] = lambda: _profesor_session(auth.id, tenant)
    resp = await p_client.put("/api/perfil", json={"regional": "Rosario"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["regional"] == "Rosario"
    assert data["nombre"] == "Nombre"


@pytest.mark.asyncio
async def test_get_perfil_sin_auth_401(p_client, p_app, db_session, tenant):
    resp = await p_client.get("/api/perfil")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_perfil_tenant_isolation(p_client, p_app, db_session, tenant):
    await _seed_perfil_permiso(db_session, tenant)
    auth, u = await _create_usuario(db_session, tenant, "iso_perfil@test.com", "Iso")

    other_tenant_id = uuid.uuid4()
    p_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=auth.id, tenant_id=other_tenant_id, roles=["PROFESOR"],
    )
    resp = await p_client.get("/api/perfil")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_put_perfil_facturador(p_client, p_app, db_session, tenant):
    await _seed_perfil_permiso(db_session, tenant)
    auth, u = await _create_usuario(db_session, tenant, "put_fact@test.com", "Fact")

    p_app.dependency_overrides[get_current_user] = lambda: _profesor_session(auth.id, tenant)
    resp = await p_client.put("/api/perfil", json={"facturador": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["facturador"] is True
