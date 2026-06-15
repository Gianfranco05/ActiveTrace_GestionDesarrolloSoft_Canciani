"""E2E integration test: preview → confirm → list → vaciar."""

from datetime import date
import io
import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from openpyxl import Workbook
from sqlalchemy import select

from app.api.v1.routers.padron import router as padron_router
from app.core.dependencies import UserSession, get_current_user, get_db
from app.models.padron import EntradaPadron, VersionPadron
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte


def _make_xlsx(rows: list[dict] | None = None) -> bytes:
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


async def _seed_permisos(db_session, tenant) -> Rol:
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


async def _create_materia(db_session, tenant, codigo: str) -> Materia:
    m = Materia(codigo=codigo, nombre="Test Materia", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


async def _create_cohorte(db_session, tenant) -> Cohorte:
    c = Carrera(codigo="INT-CAR-001", nombre="Test Carrera", tenant_id=tenant.id)
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    co = Cohorte(
        carrera_id=c.id,
        nombre="INT-2026",
        anio=2026,
        vig_desde=date(2026, 1, 1),
        tenant_id=tenant.id,
    )
    db_session.add(co)
    await db_session.commit()
    await db_session.refresh(co)
    return co


async def _create_test_usuario(db_session, tenant) -> Usuario:
    auth_user = AuthUser(tenant_id=tenant.id, email="integ@test.com", password_hash="hash")
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)
    usuario = Usuario(id=auth_user.id, tenant_id=tenant.id, nombre="Integ", apellidos="Test")
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


@pytest.mark.asyncio
async def test_e2e_preview_confirm_list_vaciar(http_client, test_app, db_session, tenant):
    """Full E2E: preview file → confirm import → verify version + entries → vaciar."""
    await _seed_permisos(db_session, tenant)
    usuario = await _create_test_usuario(db_session, tenant)
    materia = await _create_materia(db_session, tenant, "INT-MAT-001")
    cohorte = await _create_cohorte(db_session, tenant)

    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=usuario.id, tenant_id=tenant.id, roles=["ADMIN"],
    )

    # ── Step 1: Preview ──
    xlsx_bytes = _make_xlsx([
        {"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com"},
        {"nombre": "Maria", "apellidos": "Lopez", "email": "maria@test.com"},
    ])
    preview_resp = await http_client.post(
        "/api/v1/padron/importar/preview",
        files={"file": ("test.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert preview_resp.status_code == 200, f"Preview failed: {preview_resp.text}"
    preview_data = preview_resp.json()
    assert preview_data["total_rows"] == 2
    assert len(preview_data["rows"]) == 2
    assert preview_data["rows"][0]["nombre"] == "Juan"

    # ── Step 2: Confirm ──
    confirm_resp = await http_client.post(
        "/api/v1/padron/importar/confirmar",
        json={
            "entries": [
                {"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com"},
                {"nombre": "Maria", "apellidos": "Lopez", "email": "maria@test.com"},
            ],
            "materia_id": str(materia.id),
            "cohorte_id": str(cohorte.id),
        },
    )
    assert confirm_resp.status_code == 201, f"Confirm failed: {confirm_resp.text}"
    version_data = confirm_resp.json()
    version_id = version_data["id"]
    assert version_data["activa"] is True
    assert version_data["materia_id"] == str(materia.id)
    assert version_data["cohorte_id"] == str(cohorte.id)

    # ── Step 3: List versiones ──
    list_resp = await http_client.get("/api/v1/padron/versiones")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    ids = [v["id"] for v in list_data["items"]]
    assert version_id in ids

    # ── Step 4: Get version detail ──
    detail_resp = await http_client.get(f"/api/v1/padron/versiones/{version_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["id"] == version_id
    assert detail_data["activa"] is True

    # ── Step 5: List entradas ──
    entradas_resp = await http_client.get(f"/api/v1/padron/versiones/{version_id}/entradas")
    assert entradas_resp.status_code == 200
    entradas_data = entradas_resp.json()
    assert entradas_data["total"] == 2
    nombres = {e["nombre"] for e in entradas_data["items"]}
    assert nombres == {"Juan", "Maria"}

    # ── Step 6: Verify entries in DB (not soft-deleted) via ORM ──
    version_uuid = uuid.UUID(version_id)
    all_entries = await db_session.execute(
        select(EntradaPadron).where(
            EntradaPadron.version_id == version_uuid,
            EntradaPadron.deleted_at.is_(None),
        )
    )
    assert len(all_entries.scalars().all()) == 2

    # ── Step 7: Deactivate version first, then vaciar ──
    version_db = await db_session.get(VersionPadron, version_uuid)
    version_db.activa = False
    await db_session.commit()

    vaciar_resp = await http_client.post(f"/api/v1/padron/versiones/{version_id}/vaciar")
    assert vaciar_resp.status_code == 200, f"Vaciar failed: {vaciar_resp.text}"
    vaciar_data = vaciar_resp.json()
    assert vaciar_data["deleted_entries"] == 2
    assert vaciar_data["version_id"] == version_id

    # ── Step 8: Verify entries soft-deleted via API ──
    entradas_resp = await http_client.get(f"/api/v1/padron/versiones/{version_id}/entradas")
    entradas_data = entradas_resp.json()
    assert entradas_data["total"] == 0
