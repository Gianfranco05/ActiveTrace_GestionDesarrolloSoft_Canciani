"""Tests for GET /api/auditoria/panel/ultimas-acciones (Task 20 / 5.4)."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.auditoria import router as auditoria_router
from app.core.dependencies import UserSession, get_current_user, get_db


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


async def _seed_ultimas_data(db_session, tenant):
    from app.models.auth_user import AuthUser
    from app.models.usuario import Usuario
    from app.models.materia import Materia
    from app.models.audit_log import AuditLog

    user_a = AuthUser(tenant_id=tenant.id, email="ult_a@test.com", password_hash="x")
    user_b = AuthUser(tenant_id=tenant.id, email="ult_b@test.com", password_hash="x")
    db_session.add_all([user_a, user_b])
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    profile_a = Usuario(tenant_id=tenant.id, id=user_a.id, nombre="Ult", apellidos="Alpha")
    profile_b = Usuario(tenant_id=tenant.id, id=user_b.id, nombre="Ult", apellidos="Beta")
    db_session.add_all([profile_a, profile_b])

    mat_a = Materia(tenant_id=tenant.id, codigo="U001", nombre="Ultima A")
    mat_b = Materia(tenant_id=tenant.id, codigo="U002", nombre="Ultima B")
    db_session.add_all([mat_a, mat_b])
    await db_session.commit()
    await db_session.refresh(mat_a)
    await db_session.refresh(mat_b)

    now = datetime.now(timezone.utc)

    for i in range(5):
        e = AuditLog(tenant_id=tenant.id, actor_id=user_a.id, materia_id=mat_a.id,
                     accion=f"ACCION_{i}", fecha_hora=now - timedelta(hours=i),
                     ip=f"10.0.0.{i}")
        db_session.add(e)
    for i in range(3):
        e = AuditLog(tenant_id=tenant.id, actor_id=user_b.id, materia_id=mat_b.id,
                     accion=f"OTHER_{i}", fecha_hora=now - timedelta(hours=i + 10),
                     ip=f"192.168.0.{i}")
        db_session.add(e)
    await db_session.commit()
    return user_a, user_b, mat_a, mat_b, now


# ─── DEFAULT LIMIT 200 ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_default_limit_200(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, _, _, _, _ = await _seed_ultimas_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/ultimas-acciones")
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_registros"] == 200


# ─── CUSTOM LIMIT ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_custom_limit_50(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, _, _, _, _ = await _seed_ultimas_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/ultimas-acciones?limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_registros"] == 50
    assert len(data["items"]) <= 50


# ─── CAP AT 1000 ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cap_at_1000(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, _, _, _, _ = await _seed_ultimas_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/ultimas-acciones?limit=1000")
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_registros"] == 1000
    assert len(data["items"]) <= 8


# ─── FILTER BY DATE RANGE ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_filter_by_date_range(http_client, test_app, db_session, tenant):
    from app.models.auth_user import AuthUser
    from app.models.audit_log import AuditLog

    await _seed_perm(db_session, tenant)
    user = AuthUser(tenant_id=tenant.id, email="datefilt@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    now = datetime.now(timezone.utc)
    day_inside = now - timedelta(days=5)
    day_outside = now - timedelta(days=20)

    e1 = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="INSIDE",
                  fecha_hora=day_inside)
    e2 = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="OUTSIDE",
                  fecha_hora=day_outside)
    db_session.add_all([e1, e2])
    await db_session.commit()

    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    desde = (now - timedelta(days=10)).date()
    hasta = (now + timedelta(days=1)).date()
    resp = await http_client.get(
        "/api/auditoria/panel/ultimas-acciones",
        params={"fecha_desde": str(desde), "fecha_hasta": str(hasta), "limit": 50},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["accion"] == "INSIDE"


# ─── FILTER BY USUARIO_ID ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_filter_by_usuario_id(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b, _, _, _ = await _seed_ultimas_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get(
        "/api/auditoria/panel/ultimas-acciones",
        params={"usuario_id": str(user_a.id), "limit": 50},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 5
    for item in data["items"]:
        assert item["actor_id"] == str(user_a.id)


# ─── FILTER BY MATERIA_ID ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_filter_by_materia_id(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b, mat_a, mat_b, _ = await _seed_ultimas_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get(
        "/api/auditoria/panel/ultimas-acciones",
        params={"materia_id": str(mat_b.id), "limit": 50},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 3
    for item in data["items"]:
        assert item["materia_id"] == str(mat_b.id)


# ─── COORDINADOR SCOPE ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_coordinador_scope(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b, _, _, _ = await _seed_ultimas_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user_a.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "COORDINADOR"],
    )

    resp = await http_client.get("/api/auditoria/panel/ultimas-acciones?limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 5
    for item in data["items"]:
        assert item["actor_id"] == str(user_a.id)


# ─── ADMIN SCOPE ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_scope(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b, _, _, _ = await _seed_ultimas_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/ultimas-acciones?limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 8


# ─── RESOLVED NAMES ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolved_names_present(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, _, mat_a, _, _ = await _seed_ultimas_data(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/ultimas-acciones?limit=50")
    assert resp.status_code == 200
    data = resp.json()

    for item in data["items"]:
        assert "actor_nombre" in item
        assert "materia_nombre" in item

    user_a_items = [i for i in data["items"] if i["actor_id"] == str(user_a.id)]
    assert all(i["actor_nombre"] == "Ult Alpha" for i in user_a_items)

    mat_a_items = [i for i in data["items"] if i["materia_id"] == str(mat_a.id)]
    assert all(i["materia_nombre"] == "Ultima A" for i in mat_a_items)
