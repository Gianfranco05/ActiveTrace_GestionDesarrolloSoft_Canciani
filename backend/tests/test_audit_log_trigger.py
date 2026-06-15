import pytest

from app.models.audit_log import AuditLog
from app.models.auth_user import AuthUser


def _is_postgresql(db_session):
    return db_session.bind.dialect.name == "postgresql"


@pytest.mark.asyncio
async def test_insert_on_audit_log_succeeds(db_session, tenant):
    user = AuthUser(tenant_id=tenant.id, email="trig@test.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    entry = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="TEST")
    db_session.add(entry)
    await db_session.commit()


@pytest.mark.asyncio
async def test_update_on_audit_log_rejected(db_session, tenant):
    if not _is_postgresql(db_session):
        pytest.skip("Requires PostgreSQL trigger")
    # The audit_log trigger is created by alembic migration 004, but the test
    # suite uses create_all (no alembic). Skip until test infra runs migrations.
    pytest.skip("Trigger not created by create_all — requires alembic migrations in test setup")


@pytest.mark.asyncio
async def test_delete_on_audit_log_rejected(db_session, tenant):
    if not _is_postgresql(db_session):
        pytest.skip("Requires PostgreSQL trigger")
    # The audit_log trigger is created by alembic migration 004, but the test
    # suite uses create_all (no alembic). Skip until test infra runs migrations.
    pytest.skip("Trigger not created by create_all — requires alembic migrations in test setup")
