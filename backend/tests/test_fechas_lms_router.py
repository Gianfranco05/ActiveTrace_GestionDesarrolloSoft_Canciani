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
def lms_test_app(db_session):
    app = FastAPI()
    app.include_router(fa_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def lms_http_client(lms_test_app):
    transport = ASGITransport(app=lms_test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _lms_seed_permiso(db_session, tenant):
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


async def _lms_seed_data(db_session, tenant):
    suffix = uuid.uuid4().hex[:8]
    c = Carrera(id=uuid.uuid4(), codigo=f"LMS-{suffix}", nombre="Test C", tenant_id=tenant.id)
    db_session.add(c)
    m = Materia(id=uuid.uuid4(), codigo=f"LMS-M{suffix}", nombre="Programacion I", tenant_id=tenant.id)
    db_session.add(m)
    co = Cohorte(id=uuid.uuid4(), carrera_id=c.id, nombre=f"LMS-C{suffix}", anio=2026, vig_desde=date(2026, 1, 1), tenant_id=tenant.id)
    db_session.add(co)
    await db_session.commit()
    return c, m, co


@pytest.mark.asyncio
async def test_lms_html_200(lms_http_client, lms_test_app, db_session, tenant):
    await _lms_seed_permiso(db_session, tenant)
    lms_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _lms_seed_data(db_session, tenant)

    await lms_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id),
        "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
        "fecha": "2026-04-15", "titulo": "Primer Parcial",
    })

    resp = await lms_http_client.get(f"/api/fechas-academicas/lms/html?materia_id={m.id}&cohorte_id={co.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "html" in data
    assert isinstance(data["html"], str)
    assert "<table" in data["html"]
    assert "Primer Parcial" in data["html"]


@pytest.mark.asyncio
async def test_lms_html_table_has_columns(lms_http_client, lms_test_app, db_session, tenant):
    await _lms_seed_permiso(db_session, tenant)
    lms_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _lms_seed_data(db_session, tenant)

    await lms_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id),
        "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
        "fecha": "2026-04-15", "titulo": "P1",
    })

    resp = await lms_http_client.get(f"/api/fechas-academicas/lms/html?materia_id={m.id}&cohorte_id={co.id}")
    html = resp.json()["html"]
    assert "Fecha" in html
    assert "Tipo" in html
    assert "Instancia" in html
    assert "Título" in html


@pytest.mark.asyncio
async def test_lms_html_empty_materia_returns_info(lms_http_client, lms_test_app, db_session, tenant):
    await _lms_seed_permiso(db_session, tenant)
    lms_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _lms_seed_data(db_session, tenant)

    resp = await lms_http_client.get(f"/api/fechas-academicas/lms/html?materia_id={m.id}&cohorte_id={co.id}")
    assert resp.status_code == 200
    html = resp.json()["html"]
    assert "Programacion I" in html
    assert "no hay fechas" in html.lower()


@pytest.mark.asyncio
async def test_lms_html_404_missing_materia(lms_http_client, lms_test_app, db_session, tenant):
    await _lms_seed_permiso(db_session, tenant)
    lms_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await lms_http_client.get(f"/api/fechas-academicas/lms/html?materia_id={uuid.uuid4()}&cohorte_id={uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_lms_html_403_without_permission(lms_http_client, lms_test_app, db_session, tenant):
    await _lms_seed_permiso(db_session, tenant)
    lms_test_app.dependency_overrides[get_current_user] = lambda: _unauthorized_session(tenant)
    c, m, co = await _lms_seed_data(db_session, tenant)

    resp = await lms_http_client.get(f"/api/fechas-academicas/lms/html?materia_id={m.id}&cohorte_id={co.id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_lms_html_no_external_css(lms_http_client, lms_test_app, db_session, tenant):
    await _lms_seed_permiso(db_session, tenant)
    lms_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _lms_seed_data(db_session, tenant)

    await lms_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id),
        "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
        "fecha": "2026-04-15", "titulo": "P1",
    })

    resp = await lms_http_client.get(f"/api/fechas-academicas/lms/html?materia_id={m.id}&cohorte_id={co.id}")
    html = resp.json()["html"]
    assert "<link" not in html


@pytest.mark.asyncio
async def test_lms_html_excludes_soft_deleted(lms_http_client, lms_test_app, db_session, tenant):
    await _lms_seed_permiso(db_session, tenant)
    lms_test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _lms_seed_data(db_session, tenant)

    create_resp = await lms_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id),
        "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
        "fecha": "2026-04-15", "titulo": "Keep",
    })
    await lms_http_client.post("/api/fechas-academicas", json={
        "materia_id": str(m.id), "cohorte_id": str(co.id),
        "tipo": "TP", "numero": 1, "periodo": "2026-1",
        "fecha": "2026-05-10", "titulo": "Delete",
    })

    fa_id = create_resp.json()["id"]
    await lms_http_client.delete(f"/api/fechas-academicas/{fa_id}")

    resp = await lms_http_client.get(f"/api/fechas-academicas/lms/html?materia_id={m.id}&cohorte_id={co.id}")
    html = resp.json()["html"]
    assert "Keep" not in html
    assert "Delete" in html
