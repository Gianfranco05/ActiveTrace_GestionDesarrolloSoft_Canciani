import uuid
from datetime import date

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.fechas_academicas import router as fa_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso


@pytest.fixture
def fa_test_app(db_session):
    app = FastAPI()
    app.include_router(fa_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def fa_http_client(fa_test_app):
    transport = ASGITransport(app=fa_test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _fa_seed_permiso(db_session, tenant):
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


def _admin_session(tenant):
    return UserSession(user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["ADMIN"])


def _unauthorized_session(tenant):
    return UserSession(user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["ALUMNO"])


async def _fa_seed_data(db_session, tenant):
    suffix = uuid.uuid4().hex[:8]
    c = Carrera(id=uuid.uuid4(), codigo=f"F-T{suffix}", nombre="Test C", tenant_id=tenant.id)
    db_session.add(c)
    m = Materia(id=uuid.uuid4(), codigo=f"F-M{suffix}", nombre="Test M", tenant_id=tenant.id)
    db_session.add(m)
    co = Cohorte(id=uuid.uuid4(), carrera_id=c.id, nombre=f"F-C{suffix}", anio=2026, vig_desde=date(2026, 1, 1), tenant_id=tenant.id)
    db_session.add(co)
    await db_session.commit()
    return c, m, co


@pytest.mark.asyncio
async def test_create_fecha_201(fa_http_client, fa_test_app, db_session, tenant):
    await _fa_seed_permiso(db_session, tenant)
    fa_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _fa_seed_data(db_session, tenant)

    resp = await fa_http_client.post(
        "/api/fechas-academicas",
        json={
            "materia_id": str(m.id),
            "cohorte_id": str(co.id),
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": "2026-04-15",
            "titulo": "Primer Parcial",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["tipo"] == "Parcial"
    assert data["numero"] == 1
    assert data["periodo"] == "2026-1"


@pytest.mark.asyncio
async def test_list_200(fa_http_client, fa_test_app, db_session, tenant):
    await _fa_seed_permiso(db_session, tenant)
    fa_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _fa_seed_data(db_session, tenant)

    await fa_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id), "tipo": "Parcial",
        "numero": 1, "periodo": "2026-1", "fecha": "2026-04-15", "titulo": "P1",
    })

    resp = await fa_http_client.get("/api/fechas-academicas")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_by_tipo(fa_http_client, fa_test_app, db_session, tenant):
    await _fa_seed_permiso(db_session, tenant)
    fa_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _fa_seed_data(db_session, tenant)

    await fa_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id), "tipo": "Parcial",
        "numero": 1, "periodo": "2026-1", "fecha": "2026-04-15",
    })
    await fa_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id), "tipo": "Coloquio",
        "numero": 1, "periodo": "2026-1", "fecha": "2026-06-20",
    })

    resp = await fa_http_client.get("/api/fechas-academicas?tipo=Parcial")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["tipo"] == "Parcial"


@pytest.mark.asyncio
async def test_list_by_periodo(fa_http_client, fa_test_app, db_session, tenant):
    await _fa_seed_permiso(db_session, tenant)
    fa_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _fa_seed_data(db_session, tenant)

    await fa_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id), "tipo": "Parcial",
        "numero": 1, "periodo": "2026-1", "fecha": "2026-04-15",
    })
    await fa_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id), "tipo": "Parcial",
        "numero": 1, "periodo": "2026-2", "fecha": "2026-09-15",
    })

    resp = await fa_http_client.get("/api/fechas-academicas?periodo=2026-2")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["periodo"] == "2026-2"


@pytest.mark.asyncio
async def test_calendario_200(fa_http_client, fa_test_app, db_session, tenant):
    await _fa_seed_permiso(db_session, tenant)
    fa_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _fa_seed_data(db_session, tenant)

    await fa_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id), "tipo": "Parcial",
        "numero": 1, "periodo": "2026-1", "fecha": "2026-04-15",
    })

    resp = await fa_http_client.get(f"/api/fechas-academicas/calendario?materia_id={m.id}&cohorte_id={co.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_calendario_date_range(fa_http_client, fa_test_app, db_session, tenant):
    await _fa_seed_permiso(db_session, tenant)
    fa_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _fa_seed_data(db_session, tenant)

    await fa_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id), "tipo": "Parcial",
        "numero": 1, "periodo": "2026-1", "fecha": "2026-04-15",
    })
    await fa_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id), "tipo": "Parcial",
        "numero": 2, "periodo": "2026-1", "fecha": "2026-06-30",
    })

    resp = await fa_http_client.get("/api/fechas-academicas/calendario?fecha_desde=2026-05-01&fecha_hasta=2026-07-30")
    data = resp.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_calendario_empty(fa_http_client, fa_test_app, db_session, tenant):
    await _fa_seed_permiso(db_session, tenant)
    fa_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _fa_seed_data(db_session, tenant)

    resp = await fa_http_client.get(f"/api/fechas-academicas/calendario?materia_id={m.id}&cohorte_id={co.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_create_403(fa_http_client, fa_test_app, db_session, tenant):
    await _fa_seed_permiso(db_session, tenant)
    fa_test_app.dependency_overrides[get_current_user] = lambda: _unauthorized_session(tenant)
    c, m, co = await _fa_seed_data(db_session, tenant)

    resp = await fa_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id), "tipo": "Parcial",
        "numero": 1, "periodo": "2026-1", "fecha": "2026-04-15",
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_patch_200(fa_http_client, fa_test_app, db_session, tenant):
    await _fa_seed_permiso(db_session, tenant)
    fa_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _fa_seed_data(db_session, tenant)

    create_resp = await fa_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id), "tipo": "Parcial",
        "numero": 1, "periodo": "2026-1", "fecha": "2026-04-15", "titulo": "Original",
    })
    fa_id = create_resp.json()["id"]

    resp = await fa_http_client.patch(f"/api/fechas-academicas/{fa_id}", json={"titulo": "Modificado"})
    assert resp.status_code == 200
    assert resp.json()["titulo"] == "Modificado"
    assert resp.json()["tipo"] == "Parcial"


@pytest.mark.asyncio
async def test_patch_404(fa_http_client, fa_test_app, db_session, tenant):
    await _fa_seed_permiso(db_session, tenant)
    fa_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await fa_http_client.patch(f"/api/fechas-academicas/{uuid.uuid4()}", json={"titulo": "X"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_204(fa_http_client, fa_test_app, db_session, tenant):
    await _fa_seed_permiso(db_session, tenant)
    fa_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _fa_seed_data(db_session, tenant)

    create_resp = await fa_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id), "tipo": "TP",
        "numero": 1, "periodo": "2026-1", "fecha": "2026-05-10",
    })
    fa_id = create_resp.json()["id"]

    resp = await fa_http_client.delete(f"/api/fechas-academicas/{fa_id}")
    assert resp.status_code == 204

    get_resp = await fa_http_client.patch(f"/api/fechas-academicas/{fa_id}", json={"titulo": "X"})
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_404(fa_http_client, fa_test_app, db_session, tenant):
    await _fa_seed_permiso(db_session, tenant)
    fa_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await fa_http_client.delete(f"/api/fechas-academicas/{uuid.uuid4()}")
    assert resp.status_code == 404
