import uuid
from datetime import date

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.estructura import router as estructura_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
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


async def _seed_admin_with_estructura(db_session, tenant) -> Rol:
    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo="estructura:gestionar")
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


# --- Carrera Tests ---


@pytest.mark.asyncio
async def test_list_carreras(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    c = Carrera(codigo="LIC", nombre="Licenciatura", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()

    resp = await http_client.get("/api/v1/estructura/carreras")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["codigo"] == "LIC"


@pytest.mark.asyncio
async def test_create_carrera(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.post(
        "/api/v1/estructura/carreras",
        json={"codigo": "NUEVA", "nombre": "Carrera Nueva"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["codigo"] == "NUEVA"
    assert data["nombre"] == "Carrera Nueva"
    assert data["estado"] == "Activa"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_codigo_409(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    await http_client.post(
        "/api/v1/estructura/carreras",
        json={"codigo": "DUP", "nombre": "Original"},
    )
    resp = await http_client.post(
        "/api/v1/estructura/carreras",
        json={"codigo": "DUP", "nombre": "Duplicado"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_carrera_by_id(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    c = Carrera(codigo="GET-ME", nombre="Findable", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    resp = await http_client.get(f"/api/v1/estructura/carreras/{c.id}")
    assert resp.status_code == 200
    assert resp.json()["codigo"] == "GET-ME"


@pytest.mark.asyncio
async def test_update_carrera(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    c = Carrera(codigo="UPD", nombre="Original", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    resp = await http_client.put(
        f"/api/v1/estructura/carreras/{c.id}",
        json={"nombre": "Actualizado", "estado": "Inactiva"},
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Actualizado"
    assert resp.json()["estado"] == "Inactiva"


@pytest.mark.asyncio
async def test_soft_delete_carrera(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    c = Carrera(codigo="DEL-ME", nombre="Delete Me", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    resp = await http_client.delete(f"/api/v1/estructura/carreras/{c.id}")
    assert resp.status_code == 204

    get_resp = await http_client.get(f"/api/v1/estructura/carreras/{c.id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_carrera_returns_403_without_permission(
    http_client, test_app, db_session, tenant,
):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _unauthorized_session(
        tenant,
    )

    resp = await http_client.get("/api/v1/estructura/carreras")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_carrera_returns_401_without_auth(http_client, test_app, db_session, tenant):
    resp = await http_client.get("/api/v1/estructura/carreras")
    assert resp.status_code == 401


# --- Cohorte Tests ---


@pytest.mark.asyncio
async def test_list_cohortes(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    c = Carrera(codigo="COH-LIST", nombre="Carrera", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    co = Cohorte(
        carrera_id=c.id, nombre="MAR-2026",
        anio=2026, vig_desde=date(2026, 3, 1), tenant_id=tenant.id,
    )
    db_session.add(co)
    await db_session.commit()

    resp = await http_client.get("/api/v1/estructura/cohortes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_create_cohorte(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    c = Carrera(codigo="COH-CREATE", nombre="Carrera", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    resp = await http_client.post(
        "/api/v1/estructura/cohortes",
        json={
            "carrera_id": str(c.id),
            "nombre": "AGO-2026",
            "anio": 2026,
            "vig_desde": "2026-08-01",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["nombre"] == "AGO-2026"
    assert data["estado"] == "Activa"


@pytest.mark.asyncio
async def test_create_cohorte_inactive_carrera_409(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    c = Carrera(
        codigo="COH-INACT", nombre="Inactiva",
        tenant_id=tenant.id, estado="Inactiva",
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    resp = await http_client.post(
        "/api/v1/estructura/cohortes",
        json={
            "carrera_id": str(c.id),
            "nombre": "FAIL",
            "anio": 2026,
            "vig_desde": "2026-08-01",
        },
    )
    assert resp.status_code == 409
    assert "Carrera must be active" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_list_cohortes_filter_by_carrera(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    c1 = Carrera(codigo="COH-F1", nombre="Carrera 1", tenant_id=tenant.id)
    c2 = Carrera(codigo="COH-F2", nombre="Carrera 2", tenant_id=tenant.id)
    db_session.add(c1)
    db_session.add(c2)
    await db_session.commit()
    await db_session.refresh(c1)
    await db_session.refresh(c2)

    for c in (c1, c2):
        co = Cohorte(
            carrera_id=c.id, nombre=f"COH-{c.id}",
            anio=2026, vig_desde=date(2026, 1, 1), tenant_id=tenant.id,
        )
        db_session.add(co)
    await db_session.commit()

    resp = await http_client.get(f"/api/v1/estructura/cohortes?carrera_id={c1.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_update_cohorte(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    c = Carrera(codigo="COH-UPD", nombre="Carrera", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    co = Cohorte(
        carrera_id=c.id, nombre="ORIG",
        anio=2026, vig_desde=date(2026, 1, 1), tenant_id=tenant.id,
    )
    db_session.add(co)
    await db_session.commit()
    await db_session.refresh(co)

    resp = await http_client.put(
        f"/api/v1/estructura/cohortes/{co.id}",
        json={"nombre": "UPDATED"},
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "UPDATED"


@pytest.mark.asyncio
async def test_soft_delete_cohorte(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    c = Carrera(codigo="COH-DEL", nombre="Carrera", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    co = Cohorte(
        carrera_id=c.id, nombre="DEL-ME",
        anio=2026, vig_desde=date(2026, 1, 1), tenant_id=tenant.id,
    )
    db_session.add(co)
    await db_session.commit()
    await db_session.refresh(co)

    resp = await http_client.delete(f"/api/v1/estructura/cohortes/{co.id}")
    assert resp.status_code == 204

    get_resp = await http_client.get(f"/api/v1/estructura/cohortes/{co.id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_cohorte_403_without_permission(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _unauthorized_session(tenant)

    resp = await http_client.get("/api/v1/estructura/cohortes")
    assert resp.status_code == 403


# --- Materia Tests ---


@pytest.mark.asyncio
async def test_list_materias(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    m = Materia(codigo="MAT-LIST", nombre="Materia", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()

    resp = await http_client.get("/api/v1/estructura/materias")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_create_materia(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.post(
        "/api/v1/estructura/materias",
        json={"codigo": "PROG_II", "nombre": "Programación II"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["codigo"] == "PROG_II"
    assert data["estado"] == "Activa"


@pytest.mark.asyncio
async def test_create_duplicate_materia_codigo_409(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    await http_client.post(
        "/api/v1/estructura/materias",
        json={"codigo": "DUP-MAT", "nombre": "Original"},
    )
    resp = await http_client.post(
        "/api/v1/estructura/materias",
        json={"codigo": "DUP-MAT", "nombre": "Duplicado"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_materia_by_id(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    m = Materia(codigo="GET-MAT", nombre="Findable", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)

    resp = await http_client.get(f"/api/v1/estructura/materias/{m.id}")
    assert resp.status_code == 200
    assert resp.json()["codigo"] == "GET-MAT"


@pytest.mark.asyncio
async def test_update_materia(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    m = Materia(codigo="UPD-MAT", nombre="Original", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)

    resp = await http_client.put(
        f"/api/v1/estructura/materias/{m.id}",
        json={"nombre": "Actualizada"},
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Actualizada"


@pytest.mark.asyncio
async def test_soft_delete_materia(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    m = Materia(codigo="DEL-MAT", nombre="Delete", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)

    resp = await http_client.delete(f"/api/v1/estructura/materias/{m.id}")
    assert resp.status_code == 204

    get_resp = await http_client.get(f"/api/v1/estructura/materias/{m.id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_materia_403_without_permission(http_client, test_app, db_session, tenant):
    await _seed_admin_with_estructura(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _unauthorized_session(tenant)

    resp = await http_client.get("/api/v1/estructura/materias")
    assert resp.status_code == 403
