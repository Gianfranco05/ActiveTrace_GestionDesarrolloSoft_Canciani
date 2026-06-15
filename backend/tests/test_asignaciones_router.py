"""TDD: Asignacion router tests."""

import uuid
from datetime import date

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.asignaciones import router as asignaciones_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.asignacion import Asignacion
from app.models.permiso import Permiso
from app.models.rol_permiso import RolPermiso


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(asignaciones_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_admin_with_asignaciones(db_session, tenant) -> Rol:
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


async def _create_test_usuario(db_session, tenant, email="asig@test.com") -> Usuario:
    auth_user = AuthUser(
        tenant_id=tenant.id,
        email=email,
        password_hash="hash",
    )
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)

    usuario = Usuario(
        id=auth_user.id,
        tenant_id=tenant.id,
        nombre="Asig",
        apellidos="User",
        dni="enc",
        cuil="enc",
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


async def _create_test_rol(db_session, tenant, nombre="PROFESOR") -> Rol:
    rol = Rol(nombre=nombre, tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)
    return rol


async def _create_test_materia(db_session, tenant) -> Materia:
    m = Materia(codigo="ASIG-MAT", nombre="Test Materia", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


async def _create_test_carrera(db_session, tenant) -> Carrera:
    c = Carrera(codigo="ASIG-CAR", nombre="Test Carrera", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


async def _create_test_cohorte(db_session, tenant, carrera) -> Cohorte:
    co = Cohorte(
        carrera_id=carrera.id,
        nombre="ASIG-2026",
        anio=2026,
        vig_desde=date(2026, 1, 1),
        tenant_id=tenant.id,
    )
    db_session.add(co)
    await db_session.commit()
    await db_session.refresh(co)
    return co


@pytest.mark.asyncio
async def test_create_asignacion(http_client, test_app, db_session, tenant):
    await _seed_admin_with_asignaciones(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    usuario = await _create_test_usuario(db_session, tenant)
    rol = await _create_test_rol(db_session, tenant)
    carrera = await _create_test_carrera(db_session, tenant)
    materia = await _create_test_materia(db_session, tenant)
    cohorte = await _create_test_cohorte(db_session, tenant, carrera)

    resp = await http_client.post(
        "/api/v1/asignaciones",
        json={
            "usuario_id": str(usuario.id),
            "rol_id": str(rol.id),
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "vig_desde": "2026-01-01",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["usuario_id"] == str(usuario.id)
    assert data["rol_id"] == str(rol.id)
    assert data["estado_vigencia"] == "Vigente"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_asignaciones(http_client, test_app, db_session, tenant):
    await _seed_admin_with_asignaciones(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    usuario = await _create_test_usuario(db_session, tenant)
    rol = await _create_test_rol(db_session, tenant)

    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date(2020, 1, 1),
    )
    db_session.add(a)
    await db_session.commit()

    resp = await http_client.get("/api/v1/asignaciones")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["usuario_id"] == str(usuario.id)


@pytest.mark.asyncio
async def test_get_asignacion(http_client, test_app, db_session, tenant):
    await _seed_admin_with_asignaciones(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    usuario = await _create_test_usuario(db_session, tenant)
    rol = await _create_test_rol(db_session, tenant)

    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date(2020, 1, 1),
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)

    resp = await http_client.get(f"/api/v1/asignaciones/{a.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(a.id)
    assert data["estado_vigencia"] == "Vigente"


@pytest.mark.asyncio
async def test_update_asignacion(http_client, test_app, db_session, tenant):
    await _seed_admin_with_asignaciones(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    usuario = await _create_test_usuario(db_session, tenant)
    rol = await _create_test_rol(db_session, tenant)

    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date(2020, 1, 1),
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)

    resp = await http_client.put(
        f"/api/v1/asignaciones/{a.id}",
        json={"comisiones": "A,B,C"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["comisiones"] == "A,B,C"


@pytest.mark.asyncio
async def test_soft_delete_asignacion(http_client, test_app, db_session, tenant):
    await _seed_admin_with_asignaciones(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    usuario = await _create_test_usuario(db_session, tenant)
    rol = await _create_test_rol(db_session, tenant)

    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date(2020, 1, 1),
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)

    resp = await http_client.delete(f"/api/v1/asignaciones/{a.id}")
    assert resp.status_code == 204

    get_resp = await http_client.get(f"/api/v1/asignaciones/{a.id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_asignacion_403_without_permission(http_client, test_app, db_session, tenant):
    await _seed_admin_with_asignaciones(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _unauthorized_session(tenant)

    resp = await http_client.get("/api/v1/asignaciones")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_asignacion_401_without_auth(http_client, test_app, db_session, tenant):
    resp = await http_client.get("/api/v1/asignaciones")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_asignacion_overlapping_returns_409(
    http_client, test_app, db_session, tenant,
):
    await _seed_admin_with_asignaciones(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    usuario = await _create_test_usuario(db_session, tenant)
    rol = await _create_test_rol(db_session, tenant)

    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date(2020, 1, 1),
    )
    db_session.add(a)
    await db_session.commit()

    resp = await http_client.post(
        "/api/v1/asignaciones",
        json={
            "usuario_id": str(usuario.id),
            "rol_id": str(rol.id),
            "vig_desde": "2020-06-01",
        },
    )
    assert resp.status_code == 409
    assert "Overlapping" in resp.json()["detail"]
