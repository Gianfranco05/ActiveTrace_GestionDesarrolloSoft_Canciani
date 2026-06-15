import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.estructura import router as estructura_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(estructura_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _get_or_create_permiso(db_session) -> Permiso:
    from sqlalchemy import select

    stmt = select(Permiso).where(Permiso.codigo == "estructura:gestionar")
    result = await db_session.execute(stmt)
    permiso = result.scalar_one_or_none()
    if permiso is None:
        permiso = Permiso(codigo="estructura:gestionar")
        db_session.add(permiso)
        await db_session.commit()
        await db_session.refresh(permiso)
    return permiso


async def _seed_admin(db_session, tenant) -> Rol:
    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)

    permiso = await _get_or_create_permiso(db_session)
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


@pytest.mark.asyncio
async def test_full_estructura_flow(http_client, test_app, db_session, tenant_a, tenant_b):
    """Full flow: create carrera → create cohorte → create materia → verify tenant isolation."""
    await _seed_admin(db_session, tenant_a)
    await _seed_admin(db_session, tenant_b)

    # Work as tenant_a
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant_a)

    resp = await http_client.post(
        "/api/v1/estructura/carreras",
        json={"codigo": "LIC-INFO", "nombre": "Licenciatura en Informática"},
    )
    assert resp.status_code == 201
    carrera_a_id = resp.json()["id"]

    resp = await http_client.post(
        "/api/v1/estructura/cohortes",
        json={
            "carrera_id": carrera_a_id,
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
        },
    )
    assert resp.status_code == 201
    cohorte_a_id = resp.json()["id"]

    resp = await http_client.post(
        "/api/v1/estructura/materias",
        json={"codigo": "PROG_I", "nombre": "Programación I"},
    )
    assert resp.status_code == 201
    materia_a_id = resp.json()["id"]

    # Verify tenant_a can see their data
    resp = await http_client.get("/api/v1/estructura/carreras")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    resp = await http_client.get("/api/v1/estructura/cohortes")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    resp = await http_client.get("/api/v1/estructura/materias")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    # Switch to tenant_b
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant_b)

    # No data visible for tenant_b
    resp = await http_client.get("/api/v1/estructura/carreras")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    resp = await http_client.get("/api/v1/estructura/cohortes")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    resp = await http_client.get("/api/v1/estructura/materias")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    # tenant_a data not accessible from tenant_b
    resp = await http_client.get(f"/api/v1/estructura/carreras/{carrera_a_id}")
    assert resp.status_code == 404

    resp = await http_client.get(f"/api/v1/estructura/cohortes/{cohorte_a_id}")
    assert resp.status_code == 404

    resp = await http_client.get(f"/api/v1/estructura/materias/{materia_a_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_cohorte_with_inactive_carrera_flow(
    http_client, test_app, db_session, tenant,
):
    """Verify business rule: inactive carrera blocks cohort creation."""
    await _seed_admin(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.post(
        "/api/v1/estructura/carreras",
        json={"codigo": "INACT", "nombre": "Inactiva", "estado": "Inactiva"},
    )
    assert resp.status_code == 201
    carrera_id = resp.json()["id"]

    resp = await http_client.post(
        "/api/v1/estructura/cohortes",
        json={
            "carrera_id": carrera_id,
            "nombre": "FAIL",
            "anio": 2026,
            "vig_desde": "2026-03-01",
        },
    )
    assert resp.status_code == 409
    assert "Carrera must be active" in resp.json()["detail"]
