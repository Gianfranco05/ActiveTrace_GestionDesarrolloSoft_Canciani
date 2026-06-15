"""TDD: Analisis router integration tests."""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.analisis import router as analisis_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.calificacion import Calificacion
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.padron import EntradaPadron, VersionPadron
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.usuario import Usuario
from app.models.auth_user import AuthUser
from app.models.audit_log import AuditLog


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(analisis_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_atrasados_permiso(db_session, tenant) -> Rol:
    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo="atrasados:ver")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(p)
    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))
    await db_session.commit()
    return rol


async def _seed_materia_cohorte(db_session, tenant):
    carrera = Carrera(codigo="RTR-CAR", nombre="Test", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)
    materia = Materia(codigo="RTR-MAT", nombre="Router Test", tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()
    await db_session.refresh(materia)
    cohorte = Cohorte(
        carrera_id=carrera.id, nombre="RTR-2026", anio=2026,
        vig_desde=datetime.now(timezone.utc).date(), tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    await db_session.commit()
    await db_session.refresh(cohorte)
    return materia, cohorte


async def _seed_padron_y_califs(db_session, tenant, materia, cohorte, usuario_id):
    vp = VersionPadron(
        tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id, activa=True,
    )
    db_session.add(vp)
    await db_session.flush()
    ep = EntradaPadron(tenant_id=tenant.id, version_id=vp.id,
                       nombre="Ana", apellidos="Lopez", email="ana@test.com")
    db_session.add(ep)
    await db_session.commit()
    await db_session.refresh(ep)
    c = Calificacion(
        tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
        entrada_padron_id=ep.id, actividad="TP1", tipo="Numerica",
        nota_numerica=80, aprobado=True, origen="Importado",
        cargado_por=usuario_id, importado_at=datetime.now(timezone.utc),
    )
    db_session.add(c)
    await db_session.commit()
    return ep


def _admin_session(usuario_id, tenant) -> UserSession:
    return UserSession(user_id=usuario_id, tenant_id=tenant.id, roles=["ADMIN"])


def _sin_permiso_session(usuario_id, tenant) -> UserSession:
    return UserSession(user_id=usuario_id, tenant_id=tenant.id, roles=["VISOR"])


# ===== Group 11: Router =====


@pytest.mark.asyncio
async def test_get_atrasados_200(http_client, test_app, db_session, tenant):
    await _seed_atrasados_permiso(db_session, tenant)
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    await _seed_padron_y_califs(db_session, tenant, materia, cohorte, usuario.id)

    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(usuario.id, tenant)
    resp = await http_client.get(f"/api/analisis/atrasados?materia_id={materia.id}&cohorte_id={cohorte.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 0


@pytest.mark.asyncio
async def test_get_ranking_200(http_client, test_app, db_session, tenant):
    await _seed_atrasados_permiso(db_session, tenant)
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    await _seed_padron_y_califs(db_session, tenant, materia, cohorte, usuario.id)

    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(usuario.id, tenant)
    resp = await http_client.get(f"/api/analisis/ranking?materia_id={materia.id}&cohorte_id={cohorte.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_get_reporte_materia_200(http_client, test_app, db_session, tenant):
    await _seed_atrasados_permiso(db_session, tenant)
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    await _seed_padron_y_califs(db_session, tenant, materia, cohorte, usuario.id)

    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(usuario.id, tenant)
    resp = await http_client.get(f"/api/analisis/reportes/materia/{materia.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["materia_id"] == str(materia.id)


@pytest.mark.asyncio
async def test_get_notas_finales_200(http_client, test_app, db_session, tenant):
    await _seed_atrasados_permiso(db_session, tenant)
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    await _seed_padron_y_califs(db_session, tenant, materia, cohorte, usuario.id)

    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(usuario.id, tenant)
    resp = await http_client.get(f"/api/analisis/notas-finales?materia_id={materia.id}&cohorte_id={cohorte.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_export_tps_csv_200(http_client, test_app, db_session, tenant):
    await _seed_atrasados_permiso(db_session, tenant)
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    await _seed_padron_y_califs(db_session, tenant, materia, cohorte, usuario.id)

    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(usuario.id, tenant)
    resp = await http_client.get(f"/api/analisis/export/tps-sin-corregir?materia_id={materia.id}&cohorte_id={cohorte.id}")
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("text/csv")


@pytest.mark.asyncio
async def test_get_monitor_general_200(http_client, test_app, db_session, tenant):
    await _seed_atrasados_permiso(db_session, tenant)
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    await _seed_padron_y_califs(db_session, tenant, materia, cohorte, usuario.id)

    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(usuario.id, tenant)
    resp = await http_client.get("/api/analisis/monitor/general")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_monitor_seguimiento_200(http_client, test_app, db_session, tenant):
    await _seed_atrasados_permiso(db_session, tenant)
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    await _seed_padron_y_califs(db_session, tenant, materia, cohorte, usuario.id)

    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(usuario.id, tenant)
    resp = await http_client.get(f"/api/analisis/monitor/seguimiento?materia_id={materia.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_monitor_coordinacion_200(http_client, test_app, db_session, tenant):
    await _seed_atrasados_permiso(db_session, tenant)
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    await _seed_padron_y_califs(db_session, tenant, materia, cohorte, usuario.id)

    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(usuario.id, tenant)
    resp = await http_client.get("/api/analisis/monitor/coordinacion")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_403_without_atrasados_ver(http_client, test_app, db_session, tenant):
    materia, cohorte = await _seed_materia_cohorte(db_session, tenant)
    usuario = await _seed_usuario(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _sin_permiso_session(usuario.id, tenant)
    resp = await http_client.get(f"/api/analisis/atrasados?materia_id={materia.id}&cohorte_id={cohorte.id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_401_without_auth(http_client, test_app, db_session, tenant):
    resp = await http_client.get("/api/analisis/atrasados")
    assert resp.status_code == 401


async def _seed_usuario(db_session, tenant):
    au = AuthUser(tenant_id=tenant.id, email="rtr@test.com", password_hash="hash")
    db_session.add(au)
    await db_session.commit()
    await db_session.refresh(au)
    u = Usuario(id=au.id, tenant_id=tenant.id, nombre="Router", apellidos="Test")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u
