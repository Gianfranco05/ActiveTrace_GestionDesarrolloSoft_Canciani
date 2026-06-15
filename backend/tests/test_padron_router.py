"""TDD: Padron router tests — preview, confirm, list, vaciar."""

from datetime import date
import io
import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from openpyxl import Workbook

from app.api.v1.routers.padron import router as padron_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.padron import VersionPadron, EntradaPadron
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte


def make_xlsx_bytes(rows: list[dict] | None = None) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(["nombre", "apellidos", "email"])
    if rows:
        for r in rows:
            ws.append([r.get("nombre", ""), r.get("apellidos", ""), r.get("email", "")])
    else:
        ws.append(["Ana", "Molina", "ana@test.com"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(padron_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_padron_permisos(db_session, tenant) -> Rol:
    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    permiso_cargar = Permiso(codigo="padron:cargar")
    permiso_ver = Permiso(codigo="padron:ver")
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
    permiso = Permiso(codigo="padron:cargar")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso)
    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=permiso.id))
    await db_session.commit()
    return rol


async def _seed_only_ver(db_session, tenant) -> Rol:
    rol = Rol(nombre="VISOR", tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo="padron:ver")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso)
    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=permiso.id))
    await db_session.commit()
    return rol


def _admin_session(tenant) -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        roles=["ADMIN"],
    )


def _cargador_session(tenant) -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        roles=["CARGADOR"],
    )


def _visor_session(tenant) -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        roles=["VISOR"],
    )


def _unauthorized_session(tenant) -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        roles=["ALUMNO"],
    )


async def _create_test_usuario(db_session, tenant) -> Usuario:
    auth_user = AuthUser(tenant_id=tenant.id, email="padron@test.com", password_hash="hash")
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)
    usuario = Usuario(id=auth_user.id, tenant_id=tenant.id, nombre="Padron", apellidos="Test")
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


_counter = 0


async def _create_test_materia(db_session, tenant) -> Materia:
    global _counter
    _counter += 1
    m = Materia(codigo=f"PAD-MAT-{_counter}", nombre="Test Materia", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


async def _create_test_cohorte(db_session, tenant) -> Cohorte:
    global _counter
    _counter += 1
    c = Carrera(codigo=f"PAD-CAR-{_counter}", nombre="Test Carrera", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    co = Cohorte(carrera_id=c.id, nombre=f"PAD-2026-{_counter}", anio=2026, vig_desde=date(2026, 1, 1), tenant_id=tenant.id)
    db_session.add(co)
    await db_session.commit()
    await db_session.refresh(co)
    return co


# ===== Section 8: Preview + Confirmar =====


@pytest.mark.asyncio
async def test_preview_import_200(http_client, test_app, db_session, tenant):
    """RED 8.1: preview endpoint returns ImportPreviewResponse."""
    await _seed_padron_permisos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    xlsx_bytes = make_xlsx_bytes()
    resp = await http_client.post(
        "/api/v1/padron/importar/preview",
        files={"file": ("test.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rows"] == 1
    assert len(data["rows"]) == 1


@pytest.mark.asyncio
async def test_preview_unsupported_format_400(http_client, test_app, db_session, tenant):
    """TRIANGULATE 8.5: unsupported format returns 400."""
    await _seed_padron_permisos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    resp = await http_client.post(
        "/api/v1/padron/importar/preview",
        files={"file": ("test.txt", b"not a valid file", "text/plain")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_403_without_padron_cargar(http_client, test_app, db_session, tenant):
    """TRIANGULATE 8.5: 403 without padron:cargar."""
    await _seed_only_ver(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _visor_session(tenant)

    xlsx_bytes = make_xlsx_bytes()
    resp = await http_client.post(
        "/api/v1/padron/importar/preview",
        files={"file": ("test.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_401_without_auth(http_client, test_app, db_session, tenant):
    """TRIANGULATE 8.5: 401 without auth token."""
    xlsx_bytes = make_xlsx_bytes()
    resp = await http_client.post(
        "/api/v1/padron/importar/preview",
        files={"file": ("test.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_confirm_import_201(http_client, test_app, db_session, tenant):
    """TRIANGULATE 8.5: confirm import creates version and returns 201."""
    await _seed_padron_permisos(db_session, tenant)
    usuario = await _create_test_usuario(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=usuario.id, tenant_id=tenant.id, roles=["ADMIN"],
    )

    resp = await http_client.post(
        "/api/v1/padron/importar/confirmar",
        json={
            "entries": [
                {"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com"},
            ],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["activa"] is True


# ===== Section 9: Versiones + Entradas =====


@pytest.mark.asyncio
async def test_list_versiones_200(http_client, test_app, db_session, tenant):
    """RED 9.1: list versiones returns paginated results."""
    await _seed_padron_permisos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    v = VersionPadron(tenant_id=tenant.id)
    db_session.add(v)
    await db_session.commit()

    resp = await http_client.get("/api/v1/padron/versiones")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert "id" in data["items"][0]


@pytest.mark.asyncio
async def test_get_version_detail_200(http_client, test_app, db_session, tenant):
    """TRIANGULATE 9.4: get version detail by id."""
    await _seed_padron_permisos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    v = VersionPadron(tenant_id=tenant.id, activa=True)
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)

    resp = await http_client.get(f"/api/v1/padron/versiones/{v.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(v.id)
    assert data["activa"] is True


@pytest.mark.asyncio
async def test_get_version_404(http_client, test_app, db_session, tenant):
    """TRIANGULATE 9.4: get non-existent version returns 404."""
    await _seed_padron_permisos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    fake_id = uuid.uuid4()
    resp = await http_client.get(f"/api/v1/padron/versiones/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_entradas_200(http_client, test_app, db_session, tenant):
    """TRIANGULATE 9.4: list entradas for a version."""
    await _seed_padron_permisos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    v = VersionPadron(tenant_id=tenant.id)
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)

    e = EntradaPadron(tenant_id=tenant.id, version_id=v.id, nombre="Ana", apellidos="Lopez")
    db_session.add(e)
    await db_session.commit()

    resp = await http_client.get(f"/api/v1/padron/versiones/{v.id}/entradas")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["nombre"] == "Ana"


@pytest.mark.asyncio
async def test_list_entradas_empty(http_client, test_app, db_session, tenant):
    """TRIANGULATE 9.4: list entradas for version with no entries."""
    await _seed_padron_permisos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    v = VersionPadron(tenant_id=tenant.id)
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)

    resp = await http_client.get(f"/api/v1/padron/versiones/{v.id}/entradas")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_filter_versiones_by_materia(http_client, test_app, db_session, tenant):
    """TRIANGULATE 9.4: filter versiones by materia_id."""
    await _seed_padron_permisos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    m1 = await _create_test_materia(db_session, tenant)
    m2 = await _create_test_materia(db_session, tenant)
    v1 = VersionPadron(tenant_id=tenant.id, materia_id=m1.id)
    v2 = VersionPadron(tenant_id=tenant.id, materia_id=m2.id)
    db_session.add_all([v1, v2])
    await db_session.commit()

    resp = await http_client.get(f"/api/v1/padron/versiones?materia_id={m1.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_filter_versiones_by_cohorte(http_client, test_app, db_session, tenant):
    """TRIANGULATE 9.4: filter versiones by cohorte_id."""
    await _seed_padron_permisos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    co1 = await _create_test_cohorte(db_session, tenant)
    co2 = await _create_test_cohorte(db_session, tenant)
    v1 = VersionPadron(tenant_id=tenant.id, cohorte_id=co1.id)
    v2 = VersionPadron(tenant_id=tenant.id, cohorte_id=co2.id)
    db_session.add_all([v1, v2])
    await db_session.commit()

    resp = await http_client.get(f"/api/v1/padron/versiones?cohorte_id={co1.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_403_without_padron_ver(http_client, test_app, db_session, tenant):
    """TRIANGULATE 9.4: 403 without padron:ver."""
    await _seed_only_cargar(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _cargador_session(tenant)

    resp = await http_client.get("/api/v1/padron/versiones")
    assert resp.status_code == 403


# ===== Section 10: Vaciar =====


@pytest.mark.asyncio
async def test_vaciar_non_active_version_200(http_client, test_app, db_session, tenant):
    """RED 10.1: vaciar non-active version soft-deletes entries."""
    await _seed_padron_permisos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    v = VersionPadron(tenant_id=tenant.id, activa=False)
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)

    e = EntradaPadron(tenant_id=tenant.id, version_id=v.id, nombre="Test", apellidos="User")
    db_session.add(e)
    await db_session.commit()

    resp = await http_client.post(f"/api/v1/padron/versiones/{v.id}/vaciar")
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted_entries"] == 1
    assert data["version_id"] == str(v.id)


@pytest.mark.asyncio
async def test_vaciar_active_version_409(http_client, test_app, db_session, tenant):
    """TRIANGULATE 10.4: vaciar active version returns 409."""
    await _seed_padron_permisos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    v = VersionPadron(tenant_id=tenant.id, activa=True)
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)

    resp = await http_client.post(f"/api/v1/padron/versiones/{v.id}/vaciar")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_vaciar_nonexistent_404(http_client, test_app, db_session, tenant):
    """TRIANGULATE 10.4: vaciar non-existent version returns 404."""
    await _seed_padron_permisos(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _admin_session(tenant)

    fake_id = uuid.uuid4()
    resp = await http_client.post(f"/api/v1/padron/versiones/{fake_id}/vaciar")
    assert resp.status_code == 404
