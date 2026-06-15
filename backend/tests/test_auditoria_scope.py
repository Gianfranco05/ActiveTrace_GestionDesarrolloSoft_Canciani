"""CRITICAL: Scope isolation tests for auditoria panel endpoints.

Task 5.1b: Verify that COORDINADOR sees only own audit entries,
while ADMIN sees all users in the tenant.
"""

import uuid
from datetime import datetime, timedelta, timezone

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


def _make_session(tenant, roles) -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        roles=roles,
    )


async def _seed_auditoria_perm(db_session, tenant):
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


async def _seed_two_users_audit_logs(db_session, tenant):
    """Create audit logs for TWO different users in the same tenant."""
    from app.models.auth_user import AuthUser
    from app.models.audit_log import AuditLog
    from app.models.usuario import Usuario
    from app.models.materia import Materia

    user_a = AuthUser(tenant_id=tenant.id, email="coord_a@test.com", password_hash="x")
    user_b = AuthUser(tenant_id=tenant.id, email="coord_b@test.com", password_hash="x")
    db_session.add_all([user_a, user_b])
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    profile_a = Usuario(tenant_id=tenant.id, id=user_a.id, nombre="Coord", apellidos="Alpha")
    profile_b = Usuario(tenant_id=tenant.id, id=user_b.id, nombre="Coord", apellidos="Beta")
    db_session.add_all([profile_a, profile_b])

    mat = Materia(tenant_id=tenant.id, codigo="ISO001", nombre="Materia Scope")
    db_session.add(mat)
    await db_session.commit()
    await db_session.refresh(mat)

    today = _safe_now()
    yesterday = today - timedelta(days=1)

    e_a1 = AuditLog(tenant_id=tenant.id, actor_id=user_a.id, materia_id=mat.id,
                    accion="CALIFICACIONES_CARGAR", fecha_hora=today, ip="10.0.0.1")
    e_a2 = AuditLog(tenant_id=tenant.id, actor_id=user_a.id, materia_id=mat.id,
                    accion="PADRON_CARGAR", fecha_hora=yesterday, ip="10.0.0.1")
    e_b1 = AuditLog(tenant_id=tenant.id, actor_id=user_b.id, materia_id=mat.id,
                    accion="ASIGNACION_MODIFICAR", fecha_hora=today, ip="10.0.0.2")
    e_b2 = AuditLog(tenant_id=tenant.id, actor_id=user_b.id, materia_id=mat.id,
                    accion="LIQUIDACION_CERRAR", fecha_hora=yesterday, ip="10.0.0.2")
    db_session.add_all([e_a1, e_a2, e_b1, e_b2])
    await db_session.commit()

    return user_a, user_b, mat


# ─── ACCIONES POR DÍA ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scope_acciones_por_dia_coordinador(http_client, test_app, db_session, tenant):
    await _seed_auditoria_perm(db_session, tenant)
    user_a, user_b, _ = await _seed_two_users_audit_logs(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user_a.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "COORDINADOR"],
    )

    resp = await http_client.get("/api/auditoria/panel/acciones-por-dia")
    assert resp.status_code == 200
    data = resp.json()
    total = sum(d["total_acciones"] for d in data["items"])
    assert total == 2


@pytest.mark.asyncio
async def test_scope_acciones_por_dia_admin(http_client, test_app, db_session, tenant):
    await _seed_auditoria_perm(db_session, tenant)
    user_a, user_b, _ = await _seed_two_users_audit_logs(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/acciones-por-dia")
    assert resp.status_code == 200
    data = resp.json()
    total = sum(d["total_acciones"] for d in data["items"])
    assert total == 4


# ─── INTERACCIONES ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scope_interacciones_coordinador(http_client, test_app, db_session, tenant):
    await _seed_auditoria_perm(db_session, tenant)
    user_a, user_b, _ = await _seed_two_users_audit_logs(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user_a.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "COORDINADOR"],
    )

    resp = await http_client.get("/api/auditoria/panel/interacciones")
    assert resp.status_code == 200
    data = resp.json()
    total_cantidad = sum(r["cantidad"] for r in data["items"])
    # COORDINADOR A should only see 2 actions (CALIFICACIONES_CARGAR, PADRON_CARGAR)
    assert total_cantidad == 2
    for item in data["items"]:
        assert item["usuario_id"] == str(user_a.id)


@pytest.mark.asyncio
async def test_scope_interacciones_admin(http_client, test_app, db_session, tenant):
    await _seed_auditoria_perm(db_session, tenant)
    user_a, user_b, _ = await _seed_two_users_audit_logs(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/interacciones")
    assert resp.status_code == 200
    data = resp.json()
    total_cantidad = sum(r["cantidad"] for r in data["items"])
    # ADMIN should see all 4 actions
    assert total_cantidad == 4


# ─── ULTIMAS ACCIONES ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scope_ultimas_acciones_coordinador(http_client, test_app, db_session, tenant):
    await _seed_auditoria_perm(db_session, tenant)
    user_a, user_b, _ = await _seed_two_users_audit_logs(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user_a.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "COORDINADOR"],
    )

    resp = await http_client.get("/api/auditoria/panel/ultimas-acciones?limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_registros"] == 50
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert item["actor_id"] == str(user_a.id)
        assert item["actor_id"] != str(user_b.id)


@pytest.mark.asyncio
async def test_scope_ultimas_acciones_admin(http_client, test_app, db_session, tenant):
    await _seed_auditoria_perm(db_session, tenant)
    user_a, user_b, _ = await _seed_two_users_audit_logs(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/panel/ultimas-acciones?limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 4


# ─── LOG ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scope_log_coordinador(http_client, test_app, db_session, tenant):
    await _seed_auditoria_perm(db_session, tenant)
    user_a, user_b, _ = await _seed_two_users_audit_logs(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user_a.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "COORDINADOR"],
    )

    resp = await http_client.get("/api/auditoria/log")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["actor_id"] == str(user_a.id)


@pytest.mark.asyncio
async def test_scope_log_admin(http_client, test_app, db_session, tenant):
    await _seed_auditoria_perm(db_session, tenant)
    user_a, user_b, _ = await _seed_two_users_audit_logs(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=uuid.uuid4(), tenant_id=tenant.id, roles=["AUDITOR_TEST", "ADMIN"],
    )

    resp = await http_client.get("/api/auditoria/log")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 4


# ─── COORDINADOR NUNCA VE DATOS DE OTRO USUARIO ────────────────────


@pytest.mark.asyncio
async def test_coordinador_never_sees_other_users(http_client, test_app, db_session, tenant):
    """Verify COORDINADOR (user A) NEVER sees user B's actions anywhere."""
    await _seed_auditoria_perm(db_session, tenant)
    user_a, user_b, _ = await _seed_two_users_audit_logs(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user_a.id, tenant_id=tenant.id, roles=["AUDITOR_TEST", "COORDINADOR"],
    )

    endpoints = [
        "/api/auditoria/panel/acciones-por-dia",
        "/api/auditoria/panel/interacciones",
        "/api/auditoria/panel/ultimas-acciones?limit=50",
        "/api/auditoria/log",
    ]

    for endpoint in endpoints:
        resp = await http_client.get(endpoint)
        assert resp.status_code == 200, f"Failed on {endpoint}"
        data = resp.json()
        items = data.get("items", [])
        for item in items:
            actor_field = item.get("actor_id") or item.get("usuario_id")
            if actor_field:
                assert actor_field == str(user_a.id), (
                    f"COORDINADOR saw another user's data on {endpoint}: "
                    f"expected {user_a.id}, got {actor_field}"
                )
