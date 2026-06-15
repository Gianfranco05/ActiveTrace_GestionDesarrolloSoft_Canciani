import uuid
from datetime import date
from io import BytesIO

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.programas import router as programas_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso


@pytest.fixture
def ptest_app(db_session):
    app = FastAPI()
    app.include_router(programas_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def p_http_client(ptest_app):
    transport = ASGITransport(app=ptest_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_permiso(db_session, tenant):
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


async def _seed_prog_data(db_session, tenant):
    suffix = uuid.uuid4().hex[:8]
    c = Carrera(id=uuid.uuid4(), codigo=f"R-{suffix}", nombre="Test C", tenant_id=tenant.id)
    db_session.add(c)
    m = Materia(id=uuid.uuid4(), codigo=f"RM-{suffix}", nombre="Test M", tenant_id=tenant.id)
    db_session.add(m)
    co = Cohorte(id=uuid.uuid4(), carrera_id=c.id, nombre=f"RC-{suffix}", anio=2026, vig_desde=date(2026, 1, 1), tenant_id=tenant.id)
    db_session.add(co)
    await db_session.commit()
    return c, m, co


@pytest.mark.asyncio
async def test_upload_programa_201(p_http_client, ptest_app, db_session, tenant):
    await _seed_permiso(db_session, tenant)
    ptest_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _seed_prog_data(db_session, tenant)

    pdf_content = BytesIO(b"%PDF-1.4 fake pdf content")
    resp = await p_http_client.post(
        "/api/programas",
        files={"archivo": ("programa.pdf", pdf_content, "application/pdf")},
        data={"materia_id": str(m.id), "carrera_id": str(c.id), "cohorte_id": str(co.id), "titulo": "Test Programa"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["titulo"] == "Test Programa"
    assert data["materia_id"] == str(m.id)
    assert data["referencia_archivo"] != ""


@pytest.mark.asyncio
async def test_upload_403_without_permission(p_http_client, ptest_app, db_session, tenant):
    await _seed_permiso(db_session, tenant)
    ptest_app.dependency_overrides[get_current_user] = lambda: _unauthorized_session(tenant)
    c, m, co = await _seed_prog_data(db_session, tenant)

    pdf_content = BytesIO(b"fake pdf")
    resp = await p_http_client.post(
        "/api/programas",
        files={"archivo": ("p.pdf", pdf_content, "application/pdf")},
        data={"materia_id": str(m.id), "carrera_id": str(c.id), "cohorte_id": str(co.id), "titulo": "x"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_200(p_http_client, ptest_app, db_session, tenant):
    await _seed_permiso(db_session, tenant)
    ptest_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _seed_prog_data(db_session, tenant)

    pdf = BytesIO(b"fake pdf")
    await p_http_client.post(
        "/api/programas",
        files={"archivo": ("p1.pdf", pdf, "application/pdf")},
        data={"materia_id": str(m.id), "carrera_id": str(c.id), "cohorte_id": str(co.id), "titulo": "P1"},
    )

    resp = await p_http_client.get("/api/programas")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_filtered(p_http_client, ptest_app, db_session, tenant):
    await _seed_permiso(db_session, tenant)
    ptest_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _seed_prog_data(db_session, tenant)

    pdf = BytesIO(b"fake pdf")
    await p_http_client.post(
        "/api/programas",
        files={"archivo": ("p1.pdf", pdf, "application/pdf")},
        data={"materia_id": str(m.id), "carrera_id": str(c.id), "cohorte_id": str(co.id), "titulo": "P1"},
    )

    resp = await p_http_client.get(f"/api/programas?materia_id={m.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_by_id_200(p_http_client, ptest_app, db_session, tenant):
    await _seed_permiso(db_session, tenant)
    ptest_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _seed_prog_data(db_session, tenant)

    pdf = BytesIO(b"fake pdf")
    create_resp = await p_http_client.post(
        "/api/programas",
        files={"archivo": ("p.pdf", pdf, "application/pdf")},
        data={"materia_id": str(m.id), "carrera_id": str(c.id), "cohorte_id": str(co.id), "titulo": "Get Me"},
    )
    prog_id = create_resp.json()["id"]

    resp = await p_http_client.get(f"/api/programas/{prog_id}")
    assert resp.status_code == 200
    assert resp.json()["titulo"] == "Get Me"


@pytest.mark.asyncio
async def test_get_by_id_404(p_http_client, ptest_app, db_session, tenant):
    await _seed_permiso(db_session, tenant)
    ptest_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await p_http_client.get(f"/api/programas/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_204(p_http_client, ptest_app, db_session, tenant):
    await _seed_permiso(db_session, tenant)
    ptest_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _seed_prog_data(db_session, tenant)

    pdf = BytesIO(b"fake pdf")
    create_resp = await p_http_client.post(
        "/api/programas",
        files={"archivo": ("p.pdf", pdf, "application/pdf")},
        data={"materia_id": str(m.id), "carrera_id": str(c.id), "cohorte_id": str(co.id), "titulo": "Del"},
    )
    prog_id = create_resp.json()["id"]

    resp = await p_http_client.delete(f"/api/programas/{prog_id}")
    assert resp.status_code == 204

    get_resp = await p_http_client.get(f"/api/programas/{prog_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_404(p_http_client, ptest_app, db_session, tenant):
    await _seed_permiso(db_session, tenant)
    ptest_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await p_http_client.delete(f"/api/programas/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_twice_404(p_http_client, ptest_app, db_session, tenant):
    await _seed_permiso(db_session, tenant)
    ptest_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    c, m, co = await _seed_prog_data(db_session, tenant)

    pdf = BytesIO(b"fake pdf")
    create_resp = await p_http_client.post(
        "/api/programas",
        files={"archivo": ("p.pdf", pdf, "application/pdf")},
        data={"materia_id": str(m.id), "carrera_id": str(c.id), "cohorte_id": str(co.id), "titulo": "Double Del"},
    )
    prog_id = create_resp.json()["id"]

    await p_http_client.delete(f"/api/programas/{prog_id}")
    resp2 = await p_http_client.delete(f"/api/programas/{prog_id}")
    assert resp2.status_code == 404
