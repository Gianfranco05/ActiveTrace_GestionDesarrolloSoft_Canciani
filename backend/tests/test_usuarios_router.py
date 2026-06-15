"""TDD: Usuario router tests."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.usuarios import router as usuarios_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.core.security import encrypt
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(usuarios_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_admin_with_usuarios(db_session, tenant) -> Rol:
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
async def test_create_usuario(http_client, test_app, db_session, tenant):
    await _seed_admin_with_usuarios(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.post(
        "/api/v1/admin/usuarios",
        json={
            "email": "nuevo@test.com",
            "password": "Secure123",
            "nombre": "Juan",
            "apellidos": "Pérez",
            "dni": "12345678",
            "cuil": "20-12345678-9",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["nombre"] == "Juan"
    assert data["apellidos"] == "Pérez"
    assert data["dni"] == "12345678"
    assert "email" not in data
    assert "id" in data


@pytest.mark.asyncio
async def test_list_usuarios(http_client, test_app, db_session, tenant):
    await _seed_admin_with_usuarios(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    auth_user = AuthUser(
        tenant_id=tenant.id,
        email="list@test.com",
        password_hash="hash",
    )
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)

    usuario = Usuario(
        id=auth_user.id,
        tenant_id=tenant.id,
        nombre="List",
        apellidos="User",
        dni="encrypted_dni",
        cuil="encrypted_cuil",
    )
    db_session.add(usuario)
    await db_session.commit()

    resp = await http_client.get("/api/v1/admin/usuarios")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    item = data["items"][0]
    assert item["nombre"] == "List"
    # Safe response — PII must NOT be in list
    assert "dni" not in item
    assert "cuil" not in item


@pytest.mark.asyncio
async def test_get_usuario(http_client, test_app, db_session, tenant):
    await _seed_admin_with_usuarios(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    auth_user = AuthUser(
        tenant_id=tenant.id,
        email="get@test.com",
        password_hash="hash",
    )
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)

    enc_dni = encrypt("12345678")
    enc_cuil = encrypt("20-12345678-9")

    usuario = Usuario(
        id=auth_user.id,
        tenant_id=tenant.id,
        nombre="Get",
        apellidos="User",
        dni=enc_dni,
        cuil=enc_cuil,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    resp = await http_client.get(f"/api/v1/admin/usuarios/{usuario.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nombre"] == "Get"
    # Detail response includes decrypted PII
    assert data["dni"] == "12345678"
    assert "email" not in data


@pytest.mark.asyncio
async def test_update_usuario(http_client, test_app, db_session, tenant):
    await _seed_admin_with_usuarios(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    auth_user = AuthUser(
        tenant_id=tenant.id,
        email="update@test.com",
        password_hash="hash",
    )
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)

    enc_dni = encrypt("11111111")
    enc_cuil = encrypt("20-11111111-1")

    usuario = Usuario(
        id=auth_user.id,
        tenant_id=tenant.id,
        nombre="Old",
        apellidos="Name",
        dni=enc_dni,
        cuil=enc_cuil,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    resp = await http_client.put(
        f"/api/v1/admin/usuarios/{usuario.id}",
        json={"nombre": "Updated", "apellidos": "NewName"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["nombre"] == "Updated"
    assert data["apellidos"] == "NewName"


@pytest.mark.asyncio
async def test_soft_delete_usuario(http_client, test_app, db_session, tenant):
    await _seed_admin_with_usuarios(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    auth_user = AuthUser(
        tenant_id=tenant.id,
        email="delete@test.com",
        password_hash="hash",
    )
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)

    usuario = Usuario(
        id=auth_user.id,
        tenant_id=tenant.id,
        nombre="Delete",
        apellidos="Me",
        dni=encrypt("99999999"),
        cuil=encrypt("20-99999999-9"),
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    resp = await http_client.delete(f"/api/v1/admin/usuarios/{usuario.id}")
    assert resp.status_code == 204

    get_resp = await http_client.get(f"/api/v1/admin/usuarios/{usuario.id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_usuario_403_without_permission(http_client, test_app, db_session, tenant):
    await _seed_admin_with_usuarios(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _unauthorized_session(tenant)

    resp = await http_client.get("/api/v1/admin/usuarios")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_usuario_401_without_auth(http_client, test_app, db_session, tenant):
    resp = await http_client.get("/api/v1/admin/usuarios")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_usuario_not_found(http_client, test_app, db_session, tenant):
    await _seed_admin_with_usuarios(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.get(f"/api/v1/admin/usuarios/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_usuario_not_found(http_client, test_app, db_session, tenant):
    await _seed_admin_with_usuarios(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.put(
        f"/api/v1/admin/usuarios/{uuid.uuid4()}",
        json={"nombre": "Nope"},
    )
    assert resp.status_code == 404
