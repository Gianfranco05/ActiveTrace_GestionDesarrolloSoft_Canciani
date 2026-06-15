"""Tests for GET /api/auditoria/panel/interacciones (Task 19 / 5.3)."""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.auditoria import router as auditoria_router
from app.core.dependencies import UserSession, get_current_user, get_db
from datetime import date as _date


def _safe_now():
    """Return noon UTC of today's local date — safe for date.today() range queries."""
    return datetime.combine(_date.today(), datetime.min.time().replace(hour=12), tzinfo=timezone.utc)


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(auditoria_router)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    return app


@pytest.fixture
def http_client(test_app):
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _seed_perm(db_session, tenant):
    from app.models.permiso import Permiso
    from app.models.rol import Rol
    from app.models.rol_permiso import RolPermiso

    rol = Rol(nombre="AUDITOR_TEST", tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo="auditoria:ver")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso)

    rp = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    await db_session.commit()
    return rol


async def _seed_interaccion_data(db_session, tenant):
    from app.models.auth_user import AuthUser
    from app.models.usuario import Usuario
    from app.models.materia import Materia
    from app.models.audit_log import AuditLog

    user_a = AuthUser(tenant_id=tenant.id, email="int_a@test.com", password_hash="x")
    user_b = AuthUser(tenant_id=tenant.id, email="int_b@test.com", password_hash="x")
    db_session.add_all([user_a, user_b])
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    profile_a = Usuario(tenant_id=tenant.id, id=user_a.id, nombre="Alpha", apellidos="Docente")
    profile_b = Usuario(tenant_id=tenant.id, id=user_b.id, nombre="Beta", apellidos="Profesor")
    db_session.add_all([profile_a, profile_b])

    mat_a = Materia(tenant_id=tenant.id, codigo="I001", nombre="Interaccion A")
    mat_b = Materia(tenant_id=tenant.id, codigo="I002", nombre="Interaccion B")
    db_session.add_all([mat_a, mat_b])
    await db_session.commit()
    await db_session.refresh(mat_a)
    await db_session.refresh(mat_b)

    now = _safe_now()

    e_a1 = AuditLog(tenant_id=tenant.id, actor_id=user_a.id, materia_id=mat_a.id,
                    accion="CALIFICACIONES_CARGAR", fecha_hora=now)
    e_a2 = AuditLog(tenant_id=tenant.id, actor_id=user_a.id, materia_id=mat_a.id,
                    accion="CALIFICACIONES_CARGAR", fecha_hora=now)
    e_a3 = AuditLog(tenant_id=tenant.id, actor_id=user_a.id, materia_id=mat_b.id,
                    accion="PADRON_CARGAR", fecha_hora=now)

    e_b1 = AuditLog(tenant_id=tenant.id, actor_id=user_b.id, materia_id=mat_b.id,
                    accion="ASIGNACION_MODIFICAR", fecha_hora=now)
    e_b2 = AuditLog(tenant_id=tenant.id, actor_id=user_b.id, materia_id=mat_b.id,
                    accion="ASIGNACION_MODIFICAR", fecha_hora=now)
    e_b3 = AuditLog(tenant_id=tenant.id, actor_id=user_b.id, materia_id=mat_b.id,
                    accion="ASIGNACION_MODIFICAR", fecha_hora=now)

    db_session.add_all([e_a1, e_a2, e_a3, e_b1, e_b2, e_b3])
    await db_session.commit()
    return user_a, user_b, mat_a, mat_b


# ─── CORRECT GROUPING ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_correct_grouping(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b, mat_a, mat_b = await _seed_interaccion_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/interacciones")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["items"]) == 3

    by_key = {}
    for item in data["items"]:
        key = (item["usuario_id"], item["materia_id"], item["accion"])
        by_key[key] = item["cantidad"]

    assert by_key[(str(user_a.id), str(mat_a.id), "CALIFICACIONES_CARGAR")] == 2
    assert by_key[(str(user_a.id), str(mat_b.id), "PADRON_CARGAR")] == 1
    assert by_key[(str(user_b.id), str(mat_b.id), "ASIGNACION_MODIFICAR")] == 3


# ─── SORTED BY CANTIDAD DESC ──────────────────────────────────────

@pytest.mark.asyncio
async def test_sorted_by_cantidad_desc(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    _, _, _, _ = await _seed_interaccion_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/interacciones")
    assert resp.status_code == 200
    data = resp.json()
    cantidades = [item["cantidad"] for item in data["items"]]
    assert cantidades == sorted(cantidades, reverse=True)


# ─── COORDINADOR SCOPE ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_coordinador_scope(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b, _, _ = await _seed_interaccion_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user_a.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "COORDINADOR"],
    )

    resp = await http_client.get("/api/auditoria/panel/interacciones")
    assert resp.status_code == 200
    data = resp.json()
    total = sum(r["cantidad"] for r in data["items"])
    assert total == 3
    for item in data["items"]:
        assert item["usuario_id"] == str(user_a.id)


# ─── ADMIN SCOPE ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_scope(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b, _, _ = await _seed_interaccion_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/interacciones")
    assert resp.status_code == 200
    data = resp.json()
    total = sum(r["cantidad"] for r in data["items"])
    assert total == 6


# ─── NO DATA ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_data_empty_items(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    from app.models.auth_user import AuthUser

    user = AuthUser(tenant_id=tenant.id, email="noint@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/interacciones")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


# ─── RESOLVED NAMES ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolved_names_present(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b, mat_a, mat_b = await _seed_interaccion_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/interacciones")
    assert resp.status_code == 200
    data = resp.json()

    for item in data["items"]:
        assert "usuario_nombre" in item
        assert "materia_nombre" in item

    user_a_items = [i for i in data["items"] if i["usuario_id"] == str(user_a.id)]
    assert all(i["usuario_nombre"] == "Alpha Docente" for i in user_a_items)

    mat_a_items = [i for i in data["items"] if i["materia_id"] == str(mat_a.id)]
    assert all(i["materia_nombre"] == "Interaccion A" for i in mat_a_items)
