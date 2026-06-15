"""Tests for GET /api/auditoria/panel/acciones-por-dia (Task 16 / 5.1)."""

import uuid
from datetime import date, datetime, timedelta, timezone

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


async def _seed_two_users(db_session, tenant):
    from app.models.auth_user import AuthUser
    from app.models.audit_log import AuditLog

    user_a = AuthUser(tenant_id=tenant.id, email="acc_a@test.com", password_hash="x")
    user_b = AuthUser(tenant_id=tenant.id, email="acc_b@test.com", password_hash="x")
    db_session.add_all([user_a, user_b])
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    today = _safe_now()
    yesterday = today - timedelta(days=1)

    e_a1 = AuditLog(tenant_id=tenant.id, actor_id=user_a.id, accion="LOGIN",
                    fecha_hora=today, ip="10.0.0.1")
    e_a2 = AuditLog(tenant_id=tenant.id, actor_id=user_a.id, accion="LOGOUT",
                    fecha_hora=yesterday, ip="10.0.0.1")
    e_b1 = AuditLog(tenant_id=tenant.id, actor_id=user_b.id, accion="QUERY",
                    fecha_hora=today, ip="10.0.0.2")
    e_b2 = AuditLog(tenant_id=tenant.id, actor_id=user_b.id, accion="UPDATE",
                    fecha_hora=yesterday, ip="10.0.0.2")
    db_session.add_all([e_a1, e_a2, e_b1, e_b2])
    await db_session.commit()
    return user_a, user_b


# ─── DEFAULT 30-DAY RANGE ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_default_30_day_range(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user, _ = await _seed_two_users(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/acciones-por-dia")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) > 0
    assert data["desde"] is not None
    assert data["hasta"] is not None
    today = date.today()
    assert data["desde"] == str(today - timedelta(days=30))
    assert data["hasta"] == str(today)


# ─── CUSTOM DATE RANGE ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_custom_date_range(http_client, test_app, db_session, tenant):
    from app.models.auth_user import AuthUser
    from app.models.audit_log import AuditLog

    await _seed_perm(db_session, tenant)
    user = AuthUser(tenant_id=tenant.id, email="custom@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    now = _safe_now()
    day_inside = now - timedelta(days=5)
    day_outside = now - timedelta(days=20)

    e1 = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="LOGIN",
                 fecha_hora=day_inside)
    e2 = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="QUERY",
                 fecha_hora=day_outside)
    db_session.add_all([e1, e2])
    await db_session.commit()

    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    desde = (now - timedelta(days=10)).date()
    hasta = (now + timedelta(days=1)).date()
    resp = await http_client.get(
        "/api/auditoria/panel/acciones-por-dia",
        params={"fecha_desde": str(desde), "fecha_hasta": str(hasta)},
    )
    assert resp.status_code == 200
    data = resp.json()
    total = sum(d["total_acciones"] for d in data["items"])
    assert total == 1
    assert data["desde"] == str(desde)
    assert data["hasta"] == str(hasta)


# ─── SCOPE ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_coordinador_scope(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b = await _seed_two_users(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user_a.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "COORDINADOR"],
    )

    resp = await http_client.get("/api/auditoria/panel/acciones-por-dia")
    assert resp.status_code == 200
    data = resp.json()
    total = sum(d["total_acciones"] for d in data["items"])
    assert total == 2


@pytest.mark.asyncio
async def test_admin_scope(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b = await _seed_two_users(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/acciones-por-dia")
    assert resp.status_code == 200
    data = resp.json()
    total = sum(d["total_acciones"] for d in data["items"])
    assert total == 4


@pytest.mark.asyncio
async def test_finanzas_scope(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    user_a, user_b = await _seed_two_users(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "FINANZAS"],
    )

    resp = await http_client.get("/api/auditoria/panel/acciones-por-dia")
    assert resp.status_code == 200
    data = resp.json()
    total = sum(d["total_acciones"] for d in data["items"])
    assert total == 4


# ─── NO DATA ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_data_empty_items(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    from app.models.auth_user import AuthUser

    user = AuthUser(tenant_id=tenant.id, email="nodata@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/acciones-por-dia")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


# ─── RESPONSE FORMAT ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_response_has_items_desde_hasta(http_client, test_app, db_session, tenant):
    await _seed_perm(db_session, tenant)
    from app.models.auth_user import AuthUser
    from app.models.audit_log import AuditLog

    user = AuthUser(tenant_id=tenant.id, email="format@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    today = _safe_now()
    AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="LOGIN",
             fecha_hora=today)
    await db_session.commit()

    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/acciones-por-dia")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "desde" in data
    assert "hasta" in data
    assert isinstance(data["items"], list)
    if data["items"]:
        assert "dia" in data["items"][0]
        assert "total_acciones" in data["items"][0]
