"""TDD: Seed de permisos encuentros:gestionar."""

import pytest
from sqlalchemy import select

from app.core.audit_codes import AuditAction
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso


@pytest.mark.asyncio
async def test_permiso_encuentros_gestionar_exists(db_session, tenant):
    p = Permiso(codigo="encuentros:gestionar")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    result = await db_session.execute(
        select(Permiso).where(Permiso.codigo == "encuentros:gestionar"),
    )
    permiso = result.scalar_one()
    assert permiso.codigo == "encuentros:gestionar"
    assert permiso.id is not None


@pytest.mark.asyncio
async def test_permiso_asociado_a_profesor(db_session, tenant):
    rol = Rol(nombre="PROFESOR", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo="encuentros:gestionar")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(p)

    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))
    await db_session.commit()

    rp_result = await db_session.execute(
        select(RolPermiso).where(
            RolPermiso.rol_id == rol.id,
            RolPermiso.permiso_id == p.id,
        ),
    )
    assert rp_result.scalar_one() is not None


@pytest.mark.asyncio
async def test_permiso_asociado_a_coordinador(db_session, tenant):
    rol = Rol(nombre="COORDINADOR", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo="encuentros:gestionar")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(p)

    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))
    await db_session.commit()

    rp_result = await db_session.execute(
        select(RolPermiso).where(
            RolPermiso.rol_id == rol.id,
            RolPermiso.permiso_id == p.id,
        ),
    )
    assert rp_result.scalar_one() is not None


@pytest.mark.asyncio
async def test_permiso_asociado_a_admin(db_session, tenant):
    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo="encuentros:gestionar")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(rol)
    await db_session.refresh(p)

    db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))
    await db_session.commit()

    rp_result = await db_session.execute(
        select(RolPermiso).where(
            RolPermiso.rol_id == rol.id,
            RolPermiso.permiso_id == p.id,
        ),
    )
    assert rp_result.scalar_one() is not None


def test_audit_codes_encuentros_existen():
    assert AuditAction.ENCUENTRO_CREAR == "ENCUENTRO_CREAR"
    assert AuditAction.ENCUENTRO_EDITAR == "ENCUENTRO_EDITAR"
    assert AuditAction.GUARDIA_REGISTRAR == "GUARDIA_REGISTRAR"
