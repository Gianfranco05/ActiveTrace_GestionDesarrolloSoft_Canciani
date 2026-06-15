import uuid

import pytest

from app.core.audit_codes import AuditAction
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditLogRepository


@pytest.fixture
async def _seed_user(db_session, tenant):
    from app.models.auth_user import AuthUser

    user = AuthUser(tenant_id=tenant.id, email="audit_repo@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_audit_log(db_session, tenant, _seed_user):
    repo = AuditLogRepository(db_session, tenant.id)
    entry = AuditLog(
        tenant_id=tenant.id,
        actor_id=_seed_user.id,
        accion=AuditAction.CALIFICACIONES_IMPORTAR.value,
    )
    result = await repo.create(entry)
    assert result.id is not None
    assert result.tenant_id == tenant.id
    assert result.actor_id == _seed_user.id
    assert result.accion == AuditAction.CALIFICACIONES_IMPORTAR.value


@pytest.mark.asyncio
async def test_list_empty(db_session, tenant):
    repo = AuditLogRepository(db_session, tenant.id)
    results = await repo.list()
    assert results == []


@pytest.mark.asyncio
async def test_list_filter_by_accion(db_session, tenant, _seed_user):
    repo = AuditLogRepository(db_session, tenant.id)
    e1 = AuditLog(tenant_id=tenant.id, actor_id=_seed_user.id, accion="CALIFICACIONES_IMPORTAR")
    e2 = AuditLog(tenant_id=tenant.id, actor_id=_seed_user.id, accion="PADRON_CARGAR")
    for e in (e1, e2):
        db_session.add(e)
    await db_session.commit()

    results = await repo.list(accion="CALIFICACIONES_IMPORTAR")
    assert len(results) == 1
    assert results[0].accion == "CALIFICACIONES_IMPORTAR"


@pytest.mark.asyncio
async def test_list_filter_by_actor_id(db_session, tenant, _seed_user):
    from app.models.auth_user import AuthUser

    other_user = AuthUser(tenant_id=tenant.id, email="other_repo@test.com", password_hash="x")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    repo = AuditLogRepository(db_session, tenant.id)
    e1 = AuditLog(tenant_id=tenant.id, actor_id=_seed_user.id, accion="COMUNICACION_ENVIAR")
    e2 = AuditLog(tenant_id=tenant.id, actor_id=other_user.id, accion="LIQUIDACION_CERRAR")
    for e in (e1, e2):
        db_session.add(e)
    await db_session.commit()

    results = await repo.list(actor_id=_seed_user.id)
    assert len(results) == 1
    assert results[0].actor_id == _seed_user.id


@pytest.mark.asyncio
async def test_list_filter_by_date_range(db_session, tenant, _seed_user):
    from datetime import datetime, timedelta, timezone

    repo = AuditLogRepository(db_session, tenant.id)
    e1 = AuditLog(
        tenant_id=tenant.id,
        actor_id=_seed_user.id,
        accion="ASIGNACION_MODIFICAR",
        fecha_hora=datetime.now(timezone.utc) - timedelta(days=5),
    )
    e2 = AuditLog(
        tenant_id=tenant.id,
        actor_id=_seed_user.id,
        accion="LIQUIDACION_CERRAR",
        fecha_hora=datetime.now(timezone.utc),
    )
    for e in (e1, e2):
        db_session.add(e)
    await db_session.commit()

    desde = datetime.now(timezone.utc) - timedelta(days=2)
    hasta = datetime.now(timezone.utc) + timedelta(days=1)
    results = await repo.list(fecha_desde=desde, fecha_hasta=hasta)
    assert len(results) == 1
    assert results[0].accion == "LIQUIDACION_CERRAR"


@pytest.mark.asyncio
async def test_list_tenant_isolation(db_session, tenant, tenant_b, _seed_user):
    from app.models.auth_user import AuthUser

    user_b = AuthUser(tenant_id=tenant_b.id, email="b_repo@test.com", password_hash="x")
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_b)

    repo_a = AuditLogRepository(db_session, tenant.id)
    repo_b = AuditLogRepository(db_session, tenant_b.id)

    e_a = AuditLog(tenant_id=tenant.id, actor_id=_seed_user.id, accion="PADRON_CARGAR")
    e_b = AuditLog(tenant_id=tenant_b.id, actor_id=user_b.id, accion="LIQUIDACION_CERRAR")
    for e in (e_a, e_b):
        db_session.add(e)
    await db_session.commit()

    results_a = await repo_a.list()
    assert len(results_a) == 1
    assert results_a[0].accion == "PADRON_CARGAR"

    results_b = await repo_b.list()
    assert len(results_b) == 1
    assert results_b[0].accion == "LIQUIDACION_CERRAR"


@pytest.mark.asyncio
async def test_list_default_pagination(db_session, tenant, _seed_user):
    repo = AuditLogRepository(db_session, tenant.id)
    from app.models.auth_user import AuthUser

    u2 = AuthUser(tenant_id=tenant.id, email="pag@test.com", password_hash="x")
    db_session.add(u2)
    await db_session.commit()

    entries = [
        AuditLog(tenant_id=tenant.id, actor_id=_seed_user.id, accion=f"ACTION_{i}")
        for i in range(5)
    ]
    for e in entries:
        db_session.add(e)
    await db_session.commit()

    results = await repo.list()
    assert len(results) == 5
    results = await repo.list(limit=2)
    assert len(results) == 2
    results = await repo.list(offset=3)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_find_by_id_returns_entry(db_session, tenant, _seed_user):
    repo = AuditLogRepository(db_session, tenant.id)
    entry = AuditLog(tenant_id=tenant.id, actor_id=_seed_user.id, accion="IMPERSONACION_INICIAR")
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)

    found = await repo.find_by_id(entry.id)
    assert found is not None
    assert found.id == entry.id
    assert found.accion == "IMPERSONACION_INICIAR"


@pytest.mark.asyncio
async def test_find_by_id_returns_none_for_wrong_tenant(db_session, tenant, tenant_b, _seed_user):
    from app.models.auth_user import AuthUser

    user_b = AuthUser(tenant_id=tenant_b.id, email="wrong_t@test.com", password_hash="x")
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_b)

    entry = AuditLog(tenant_id=tenant.id, actor_id=_seed_user.id, accion="PADRON_CARGAR")
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)

    repo_b = AuditLogRepository(db_session, tenant_b.id)
    found = await repo_b.find_by_id(entry.id)
    assert found is None


@pytest.mark.asyncio
async def test_find_by_id_returns_none_for_non_existent(db_session, tenant):
    repo = AuditLogRepository(db_session, tenant.id)
    found = await repo.find_by_id(uuid.uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_no_update_or_delete_methods(db_session, tenant):
    repo = AuditLogRepository(db_session, tenant.id)
    assert not hasattr(repo, "update")
    assert not hasattr(repo, "delete")
    assert not hasattr(repo, "soft_delete")
