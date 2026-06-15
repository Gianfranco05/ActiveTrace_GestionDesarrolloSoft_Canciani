"""TDD: Calificaciones router tests — Groups 11, 12, 13."""

from datetime import date
import io
import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from openpyxl import Workbook

from app.api.v1.routers.calificaciones import router as calificaciones_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.calificacion import UmbralMateria
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.padron import VersionPadron, EntradaPadron


def _make_xlsx_bytes(headers: list[str], rows: list[list] | None = None) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    if rows:
        for r in rows:
            ws.append(r)
    else:
        if "nombre" in headers:
            ws.append(["Ana", "Lopez", "ana@test.com"])
        else:
            ws.append(["Ana", "Lopez"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(calificaciones_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_permisos_completos(db_session, tenant) -> Rol:
    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    permiso_cargar = Permiso(codigo="calificaciones:cargar")
    permiso_ver = Permiso(codigo="calificaciones:ver")
    db_session.add_all([permiso_cargar, permiso_ver])
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso_cargar)
    await db_session.refresh(permiso_ver)
    db_session.add_all([
        RolPermiso(rol_id=rol.id, permiso_id=permiso_cargar.id),
        RolPermiso(rol_id=rol.id, permiso_id=permiso_ver.id),
    ])
    await db_session.commit()
    return rol


async def _seed_only_cargar(db_session, tenant) -> Rol:
    rol = Rol(nombre="CARGADOR", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo="calificaciones:cargar")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(p)
    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))
    await db_session.commit()
    return rol


async def _seed_only_ver(db_session, tenant) -> Rol:
    rol = Rol(nombre="VISOR", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo="calificaciones:ver")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(p)
    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))
    await db_session.commit()
    return rol


def _admin_session(tenant) -> UserSession:
    return UserSession(user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["ADMIN"])


def _cargador_session(tenant) -> UserSession:
    return UserSession(user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["CARGADOR"])


def _visor_session(tenant) -> UserSession:
    return UserSession(user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["VISOR"])


async def _create_usuario(db_session, tenant) -> Usuario:
    au = AuthUser(tenant_id=tenant.id, email="calrouter@test.com", password_hash="hash")
    db_session.add(au)
    await db_session.commit()
    await db_session.refresh(au)
    u = Usuario(id=au.id, tenant_id=tenant.id, nombre="Cal", apellidos="Router")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _create_materia(db_session, tenant) -> Materia:
    m = Materia(codigo="RTR-MAT", nombre="Router Materia", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


async def _create_cohorte(db_session, tenant) -> Cohorte:
    c = Carrera(codigo="RTR-CAR", nombre="Router Carrera", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    co = Cohorte(carrera_id=c.id, nombre="RTR-2026", anio=2026,
                 vig_desde=date(2026, 1, 1), tenant_id=tenant.id)
    db_session.add(co)
    await db_session.commit()
    await db_session.refresh(co)
    return co


async def _create_padron(db_session, tenant, materia, cohorte, usuario):
    vp = VersionPadron(tenant_id=tenant.id, materia_id=materia.id,
                       cohorte_id=cohorte.id, activa=True, cargado_por=usuario.id)
    db_session.add(vp)
    await db_session.commit()
    await db_session.refresh(vp)
    ep = EntradaPadron(tenant_id=tenant.id, version_id=vp.id,
                       nombre="Ana", apellidos="Lopez", email="ana@test.com")
    db_session.add(ep)
    await db_session.commit()
    await db_session.refresh(ep)
    return vp, ep


# ===== Group 11: Preview + Confirmar =====


@pytest.mark.asyncio
async def test_preview_import_200(http_client, test_app, db_session, tenant):
    """RED 11.1: preview returns ImportPreviewResponse."""
    await _seed_permisos_completos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    headers = ["nombre", "apellidos", "email", "TP1 (Real)", "Participacion"]
    xlsx_bytes = _make_xlsx_bytes(headers, [["Ana", "Lopez", "ana@test.com", 75, "Satisfactorio"]])
    resp = await http_client.post(
        "/api/v1/calificaciones/importar/preview",
        files={"file": ("test.xlsx", xlsx_bytes,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rows"] == 1
    assert len(data["actividades_detectadas"]) == 2


@pytest.mark.asyncio
async def test_preview_empty_file_200(http_client, test_app, db_session, tenant):
    """TRIANGULATE 11.5: empty file returns 200 with 0 rows."""
    await _seed_permisos_completos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.post(
        "/api/v1/calificaciones/importar/preview",
        files={"file": ("empty.csv", b"nombre,apellidos\n", "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rows"] == 0


@pytest.mark.asyncio
async def test_403_without_calificaciones_cargar_preview(http_client, test_app, db_session, tenant):
    """TRIANGULATE 11.5: 403 without calificaciones:cargar on preview."""
    await _seed_only_ver(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _visor_session(tenant)

    xlsx_bytes = _make_xlsx_bytes(["nombre", "apellidos"], [["Ana", "Lopez"]])
    resp = await http_client.post(
        "/api/v1/calificaciones/importar/preview",
        files={"file": ("test.xlsx", xlsx_bytes,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_401_without_auth_preview(http_client, test_app, db_session, tenant):
    """TRIANGULATE 11.5: 401 without auth token on preview."""
    xlsx_bytes = _make_xlsx_bytes(["nombre", "apellidos"], [["Ana", "Lopez"]])
    resp = await http_client.post(
        "/api/v1/calificaciones/importar/preview",
        files={"file": ("test.xlsx", xlsx_bytes,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_confirm_import_201(http_client, test_app, db_session, tenant):
    """TRIANGULATE 11.5: confirm import creates calificaciones."""
    await _seed_permisos_completos(db_session, tenant)
    usuario = await _create_usuario(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=usuario.id, tenant_id=tenant.id, roles=["ADMIN"],
    )
    materia = await _create_materia(db_session, tenant)
    cohorte = await _create_cohorte(db_session, tenant)
    await _create_padron(db_session, tenant, materia, cohorte, usuario)

    headers = ["nombre", "apellidos", "email", "TP1 (Real)"]
    xlsx_bytes = _make_xlsx_bytes(headers, [["Ana", "Lopez", "ana@test.com", 75]])
    resp = await http_client.post(
        "/api/v1/calificaciones/importar/confirmar",
        data={"materia_id": str(materia.id), "cohorte_id": str(cohorte.id)},
        files={"file": ("test.xlsx", xlsx_bytes,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["calificaciones_creadas"] >= 1
    assert data["materia_id"] == str(materia.id)


# ===== Group 12: Reporte Finalización =====


@pytest.mark.asyncio
async def test_reporte_finalizacion_200(http_client, test_app, db_session, tenant):
    """RED 12.1: reporte-finalizacion detects pending activities."""
    await _seed_permisos_completos(db_session, tenant)
    usuario = await _create_usuario(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=usuario.id, tenant_id=tenant.id, roles=["ADMIN"],
    )
    materia = await _create_materia(db_session, tenant)
    cohorte = await _create_cohorte(db_session, tenant)
    await _create_padron(db_session, tenant, materia, cohorte, usuario)

    headers = ["nombre", "apellidos", "TP Escrito", "Participacion"]
    rows = [["Ana", "Lopez", "Entregado", "Completado"]]
    xlsx_bytes = _make_xlsx_bytes(headers, rows)
    resp = await http_client.post(
        "/api/v1/calificaciones/importar/reporte-finalizacion",
        data={"materia_id": str(materia.id), "cohorte_id": str(cohorte.id)},
        files={"file": ("reporte.xlsx", xlsx_bytes,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_actividades_revisadas"] == 2
    assert len(data["posibles_sin_corregir"]) == 2


# ===== Group 13: Umbral =====


@pytest.mark.asyncio
async def test_get_umbral_200(http_client, test_app, db_session, tenant):
    """RED 13.1: GET umbral returns config."""
    await _seed_permisos_completos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    materia = await _create_materia(db_session, tenant)

    um = UmbralMateria(tenant_id=tenant.id, materia_id=materia.id, umbral_pct=75)
    um.valores_aprobatorios = ["Satisfactorio"]
    db_session.add(um)
    await db_session.commit()

    resp = await http_client.get(f"/api/v1/calificaciones/umbral?materia_id={materia.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["umbral_pct"] == 75
    assert data["materia_id"] == str(materia.id)


@pytest.mark.asyncio
async def test_get_umbral_returns_defaults(http_client, test_app, db_session, tenant):
    """TRIANGULATE 13.4: GET umbral returns defaults when no config."""
    await _seed_permisos_completos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    materia = await _create_materia(db_session, tenant)

    resp = await http_client.get(f"/api/v1/calificaciones/umbral?materia_id={materia.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["umbral_pct"] == 60


@pytest.mark.asyncio
async def test_put_umbral_200(http_client, test_app, db_session, tenant):
    """TRIANGULATE 13.4: PUT umbral creates/updates config."""
    await _seed_permisos_completos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)
    materia = await _create_materia(db_session, tenant)

    resp = await http_client.put(
        f"/api/v1/calificaciones/umbral?materia_id={materia.id}",
        json={"umbral_pct": 80},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["umbral_pct"] == 80


@pytest.mark.asyncio
async def test_get_umbral_403_without_calificaciones_ver(http_client, test_app, db_session, tenant):
    """TRIANGULATE 13.4: 403 without calificaciones:ver on GET umbral."""
    await _seed_only_cargar(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _cargador_session(tenant)
    materia = await _create_materia(db_session, tenant)

    resp = await http_client.get(f"/api/v1/calificaciones/umbral?materia_id={materia.id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_put_umbral_403_without_calificaciones_cargar(http_client, test_app, db_session, tenant):
    """TRIANGULATE 13.4: 403 without calificaciones:cargar on PUT umbral."""
    await _seed_only_ver(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _visor_session(tenant)
    materia = await _create_materia(db_session, tenant)

    resp = await http_client.put(
        f"/api/v1/calificaciones/umbral?materia_id={materia.id}",
        json={"umbral_pct": 80},
    )
    assert resp.status_code == 403
