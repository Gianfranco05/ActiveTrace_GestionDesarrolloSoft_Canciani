import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.audit import router as audit_router
from app.core.dependencies import UserSession, get_current_user, get_db


@pytest.fixture
def test_app(db_session):
    app = FastAPI()
    app.include_router(audit_router)

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


async def _seed_auditor_role(db_session, tenant):
    from app.models.permiso import Permiso
    from app.models.rol import Rol
    from app.models.rol_permiso import RolPermiso

    rol = Rol(nombre="AUDITOR", tenant_id=tenant.id)
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


async def _seed_audit_entries(db_session, tenant):
    from app.models.auth_user import AuthUser
    from app.models.audit_log import AuditLog

    user = AuthUser(tenant_id=tenant.id, email="audit_router@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    e1 = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="CALIFICACIONES_IMPORTAR")
    e2 = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="PADRON_CARGAR")
    db_session.add_all([e1, e2])
    await db_session.commit()
    await db_session.refresh(e1)
    await db_session.refresh(e2)
    return user, e1, e2


@pytest.mark.asyncio
async def test_list_audit_logs(http_client, test_app, db_session, tenant):
    await _seed_auditor_role(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _make_session(tenant, ["AUDITOR"])
    await _seed_audit_entries(db_session, tenant)

    resp = await http_client.get("/api/v1/audit")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "offset" in data
    assert "limit" in data
    assert len(data["items"]) == 2
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_filter_by_accion(http_client, test_app, db_session, tenant):
    await _seed_auditor_role(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _make_session(tenant, ["AUDITOR"])
    await _seed_audit_entries(db_session, tenant)

    resp = await http_client.get("/api/v1/audit?accion=CALIFICACIONES_IMPORTAR")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["accion"] == "CALIFICACIONES_IMPORTAR"


@pytest.mark.asyncio
async def test_list_filter_by_date_range(http_client, test_app, db_session, tenant):
    from datetime import datetime, timedelta, timezone

    await _seed_auditor_role(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _make_session(tenant, ["AUDITOR"])

    from app.models.auth_user import AuthUser
    from app.models.audit_log import AuditLog

    user = AuthUser(tenant_id=tenant.id, email="date_range@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    old = AuditLog(
        tenant_id=tenant.id, actor_id=user.id, accion="ASIGNACION_MODIFICAR",
        fecha_hora=datetime.now(timezone.utc) - timedelta(days=10),
    )
    recent = AuditLog(
        tenant_id=tenant.id, actor_id=user.id, accion="LIQUIDACION_CERRAR",
        fecha_hora=datetime.now(timezone.utc),
    )
    db_session.add_all([old, recent])
    await db_session.commit()

    desde = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
    hasta = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    resp = await http_client.get(f"/api/v1/audit?fecha_desde={desde}&fecha_hasta={hasta}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["accion"] == "LIQUIDACION_CERRAR"


@pytest.mark.asyncio
async def test_list_returns_403_without_permission(http_client, test_app, db_session, tenant):
    await _seed_auditor_role(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _make_session(tenant, ["ALUMNO"])

    resp = await http_client.get("/api/v1/audit")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_returns_401_without_auth(http_client, test_app):
    resp = await http_client.get("/api/v1/audit")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_by_id_returns_entry(http_client, test_app, db_session, tenant):
    await _seed_auditor_role(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _make_session(tenant, ["AUDITOR"])
    _, _, e2 = await _seed_audit_entries(db_session, tenant)

    resp = await http_client.get(f"/api/v1/audit/{e2.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(e2.id)
    assert data["accion"] == "PADRON_CARGAR"


@pytest.mark.asyncio
async def test_get_by_id_returns_404(http_client, test_app, db_session, tenant):
    await _seed_auditor_role(db_session, tenant)
    test_app.dependency_overrides[get_current_user] = lambda: _make_session(tenant, ["AUDITOR"])

    resp = await http_client.get(f"/api/v1/audit/{uuid.uuid4()}")
    assert resp.status_code == 404
