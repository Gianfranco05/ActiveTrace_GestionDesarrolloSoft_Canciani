import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
async def test_create_rol_permiso(db_session, tenant):
    from app.models.rol import Rol
    from app.models.permiso import Permiso
    from app.models.rol_permiso import RolPermiso

    rol = Rol(nombre="TEST_ROLE", tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo="test:action")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso)

    rp = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    await db_session.commit()
    await db_session.refresh(rp)

    assert rp.id is not None
    assert rp.rol_id == rol.id
    assert rp.permiso_id == permiso.id
    assert rp.created_at is not None


@pytest.mark.asyncio
async def test_duplicate_rol_permiso_rejected(db_session, tenant):
    from app.models.rol import Rol
    from app.models.permiso import Permiso
    from app.models.rol_permiso import RolPermiso

    rol = Rol(nombre="DUP_ROLE", tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo="test:dup")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso)

    rp1 = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp1)
    await db_session.commit()

    rp2 = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_rol_permiso_cascade_on_rol_delete(db_session, tenant):
    from app.models.rol import Rol
    from app.models.permiso import Permiso
    from app.models.rol_permiso import RolPermiso

    rol = Rol(nombre="CASCADE_ROLE", tenant_id=tenant.id)
    db_session.add(rol)
    permiso = Permiso(codigo="test:cascade")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(permiso)

    rp = RolPermiso(rol_id=rol.id, permiso_id=permiso.id)
    db_session.add(rp)
    await db_session.commit()

    await db_session.delete(rol)
    await db_session.commit()

    remaining = await db_session.execute(
        text("SELECT id FROM rol_permiso WHERE rol_id = :rid"),
        {"rid": str(rol.id)},
    )
    assert remaining.fetchone() is None
