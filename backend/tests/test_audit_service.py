import uuid

import pytest

from app.core.audit_codes import AuditAction
from app.repositories.audit_repository import AuditLogRepository
from app.services.audit_service import AuditService


@pytest.fixture
def audit_service(db_session, tenant):
    repo = AuditLogRepository(db_session, tenant.id)
    return AuditService(db_session, repo)


@pytest.fixture
async def _seed_actor(db_session, tenant):
    from app.models.auth_user import AuthUser

    user = AuthUser(tenant_id=tenant.id, email="svc_actor@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_log_creates_entry_with_all_fields(audit_service, _seed_actor, tenant):
    entry = await audit_service.log(
        accion=AuditAction.LIQUIDACION_CERRAR,
        actor_id=_seed_actor.id,
        tenant_id=tenant.id,
        detalle={"monto": 1000, "moneda": "ARS"},
        filas_afectadas=42,
        impersonado_id=None,
        materia_id=None,
        ip="10.0.0.1",
        user_agent="pytest/1.0",
    )
    assert entry.id is not None
    assert entry.accion == "LIQUIDACION_CERRAR"
    assert entry.actor_id == _seed_actor.id
    assert entry.detalle == {"monto": 1000, "moneda": "ARS"}
    assert entry.filas_afectadas == 42
    assert entry.ip == "10.0.0.1"
    assert entry.user_agent == "pytest/1.0"
    assert entry.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_log_with_defaults(audit_service, _seed_actor, tenant):
    entry = await audit_service.log(
        accion=AuditAction.PADRON_CARGAR,
        actor_id=_seed_actor.id,
        tenant_id=tenant.id,
    )
    assert entry.filas_afectadas == 0
    assert entry.detalle is None
    assert entry.impersonado_id is None
    assert entry.materia_id is None
    assert entry.ip is None
    assert entry.user_agent is None


@pytest.mark.asyncio
async def test_log_returns_entry_with_id(audit_service, _seed_actor, tenant):
    entry = await audit_service.log(
        accion=AuditAction.COMUNICACION_ENVIAR,
        actor_id=_seed_actor.id,
        tenant_id=tenant.id,
    )
    assert entry.id is not None
    assert isinstance(entry.id, uuid.UUID)


@pytest.mark.asyncio
async def test_log_with_impersonacion(audit_service, db_session, _seed_actor, tenant):
    from app.models.auth_user import AuthUser

    impersonated = AuthUser(
        tenant_id=tenant.id,
        email="impersonated_svc@test.com",
        password_hash="x",
    )
    db_session.add(impersonated)
    await db_session.commit()
    await db_session.refresh(impersonated)

    entry = await audit_service.log(
        accion=AuditAction.IMPERSONACION_INICIAR,
        actor_id=_seed_actor.id,
        tenant_id=tenant.id,
        impersonado_id=impersonated.id,
    )
    assert entry.actor_id == _seed_actor.id
    assert entry.impersonado_id == impersonated.id
