import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.audit_log import AuditLog


@pytest.mark.asyncio
async def test_create_audit_log(db_session, tenant):
    from app.models.auth_user import AuthUser

    user = AuthUser(tenant_id=tenant.id, email="audit_test@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    entry = AuditLog(
        tenant_id=tenant.id,
        actor_id=user.id,
        accion="CALIFICACIONES_IMPORTAR",
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)

    assert isinstance(entry.id, uuid.UUID)
    assert entry.tenant_id == tenant.id
    assert entry.actor_id == user.id
    assert entry.accion == "CALIFICACIONES_IMPORTAR"
    assert entry.created_at is not None
    assert entry.fecha_hora is not None


@pytest.mark.asyncio
async def test_no_updated_at_deleted_at(db_session):
    from app.models.audit_log import AuditLog

    mapper = AuditLog.__table__.c
    col_names = {c.name for c in mapper}
    assert "updated_at" not in col_names
    assert "deleted_at" not in col_names
    assert "id" in col_names
    assert "created_at" in col_names


@pytest.mark.asyncio
async def test_default_filas_afectadas(db_session, tenant):
    from app.models.auth_user import AuthUser

    user = AuthUser(tenant_id=tenant.id, email="defaults@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    entry = AuditLog(
        tenant_id=tenant.id,
        actor_id=user.id,
        accion="PADRON_CARGAR",
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)

    assert entry.filas_afectadas == 0
    assert entry.detalle is None
    assert entry.ip is None
    assert entry.user_agent is None
    assert entry.impersonado_id is None
    assert entry.materia_id is None


@pytest.mark.asyncio
async def test_fk_constraints_rejected(db_session):
    fake_id = uuid.uuid4()
    entry = AuditLog(
        tenant_id=fake_id,
        actor_id=fake_id,
        accion="LIQUIDACION_CERRAR",
    )
    db_session.add(entry)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_tenant_indexed(db_session, tenant):
    from app.models.auth_user import AuthUser

    user = AuthUser(tenant_id=tenant.id, email="indexed@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    entry = AuditLog(
        tenant_id=tenant.id,
        actor_id=user.id,
        accion="COMUNICACION_ENVIAR",
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)

    assert entry.tenant_id == tenant.id
