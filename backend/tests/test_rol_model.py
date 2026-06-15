from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
async def test_create_rol(db_session, tenant):
    from app.models.rol import Rol

    rol = Rol(
        tenant_id=tenant.id,
        nombre="ADMIN",
        descripcion="Administrator",
    )
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)

    assert rol.id is not None
    assert rol.tenant_id == tenant.id
    assert rol.nombre == "ADMIN"
    assert rol.descripcion == "Administrator"
    assert rol.created_at is not None
    assert rol.updated_at is not None
    assert rol.deleted_at is None


@pytest.mark.asyncio
async def test_rol_nombre_unique_per_tenant(db_session, tenant):
    from app.models.rol import Rol

    rol1 = Rol(tenant_id=tenant.id, nombre="UNIQUE_TEST", descripcion="First")
    db_session.add(rol1)
    await db_session.commit()

    rol2 = Rol(tenant_id=tenant.id, nombre="UNIQUE_TEST", descripcion="Duplicate")
    db_session.add(rol2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_rol_same_nombre_different_tenant_allowed(db_session, tenant_a, tenant_b):
    from app.models.rol import Rol

    rol_a = Rol(tenant_id=tenant_a.id, nombre="CROSS_TENANT")
    db_session.add(rol_a)
    await db_session.commit()

    rol_b = Rol(tenant_id=tenant_b.id, nombre="CROSS_TENANT")
    db_session.add(rol_b)
    await db_session.commit()

    assert rol_a.id != rol_b.id
    assert rol_a.tenant_id != rol_b.tenant_id


@pytest.mark.asyncio
async def test_rol_soft_delete(db_session, tenant):
    from app.models.rol import Rol

    rol = Rol(tenant_id=tenant.id, nombre="SOFT_DELETE")
    db_session.add(rol)
    await db_session.commit()
    await db_session.refresh(rol)

    assert rol.deleted_at is None

    rol.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(rol)

    assert rol.deleted_at is not None
