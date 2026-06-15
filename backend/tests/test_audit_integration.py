import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.routers.audit import router as audit_router
from app.core.audit_codes import AuditAction
from app.core.dependencies import UserSession, get_current_user, get_db
from app.repositories.audit_repository import AuditLogRepository
from app.services.audit_service import AuditService


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


async def _seed_infra(db_session, tenant):
    from app.models.permiso import Permiso
    from app.models.rol import Rol
    from app.models.rol_permiso import RolPermiso
    from app.models.auth_user import AuthUser

    user = AuthUser(tenant_id=tenant.id, email="integ@test.com", password_hash="x")
    db_session.add(user)
    rol = Rol(nombre="AUDITOR", tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo="auditoria:ver")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(rol)
    await db_session.refresh(permiso)

    rp = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    await db_session.commit()
    return user, rol


@pytest.mark.asyncio
async def test_full_audit_flow(http_client, test_app, db_session, tenant):
    user, rol = await _seed_infra(db_session, tenant)

    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user.id,
        tenant_id=tenant.id,
        roles=["AUDITOR"],
    )

    repo = AuditLogRepository(db_session, tenant.id)
    service = AuditService(db_session, repo)

    entry1 = await service.log(
        accion=AuditAction.CALIFICACIONES_IMPORTAR,
        actor_id=user.id,
        tenant_id=tenant.id,
        detalle={"archivo": "notas.csv"},
        filas_afectadas=150,
        ip="10.0.0.1",
    )
    assert entry1.id is not None

    entry2 = await service.log(
        accion=AuditAction.PADRON_CARGAR,
        actor_id=user.id,
        tenant_id=tenant.id,
        detalle={"alumnos": 50},
        filas_afectadas=50,
    )
    assert entry2.id is not None

    list_resp = await http_client.get("/api/v1/audit")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    get_resp = await http_client.get(f"/api/v1/audit/{entry1.id}")
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert detail["accion"] == "CALIFICACIONES_IMPORTAR"
    assert detail["filas_afectadas"] == 150
    assert detail["detalle"] == {"archivo": "notas.csv"}
    assert detail["ip"] == "10.0.0.1"


@pytest.mark.asyncio
async def test_audit_tenant_isolation(http_client, test_app, db_session, tenant, tenant_b):
    from app.models.auth_user import AuthUser
    from app.models.permiso import Permiso
    from app.models.rol import Rol
    from app.models.rol_permiso import RolPermiso

    user_a = AuthUser(tenant_id=tenant.id, email="iso_a@test.com", password_hash="x")
    user_b = AuthUser(tenant_id=tenant_b.id, email="iso_b@test.com", password_hash="x")
    db_session.add_all([user_a, user_b])

    auditor_a = Rol(nombre="AUDITOR", tenant_id=tenant.id)
    db_session.add(auditor_a)
    permiso = Permiso(codigo="auditoria:ver")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)
    await db_session.refresh(auditor_a)
    await db_session.refresh(permiso)

    rp = RolPermiso(rol_id=auditor_a.id, permiso_id=permiso.id)
    db_session.add(rp)
    await db_session.commit()

    repo_a = AuditLogRepository(db_session, tenant.id)
    repo_b = AuditLogRepository(db_session, tenant_b.id)
    service_a = AuditService(db_session, repo_a)
    service_b = AuditService(db_session, repo_b)

    await service_a.log(
        accion=AuditAction.COMUNICACION_ENVIAR, actor_id=user_a.id, tenant_id=tenant.id,
    )
    await service_b.log(
        accion=AuditAction.LIQUIDACION_CERRAR, actor_id=user_b.id, tenant_id=tenant_b.id,
    )

    test_app.dependency_overrides[get_current_user] = lambda: UserSession(
        user_id=user_a.id,
        tenant_id=tenant.id,
        roles=["AUDITOR"],
    )

    resp = await http_client.get("/api/v1/audit")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["accion"] == "COMUNICACION_ENVIAR"
