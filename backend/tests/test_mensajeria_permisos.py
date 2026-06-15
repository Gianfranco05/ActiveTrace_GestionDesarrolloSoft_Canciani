import pytest
from sqlalchemy import select

from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso


@pytest.mark.asyncio
async def test_permiso_mensajeria_usar_exists(db_session, tenant):
    p = Permiso(codigo="mensajeria:usar")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    result = await db_session.execute(
        select(Permiso).where(Permiso.codigo == "mensajeria:usar"),
    )
    permiso = result.scalar_one()
    assert permiso.codigo == "mensajeria:usar"
    assert permiso.id is not None


@pytest.mark.asyncio
async def test_permiso_mensajeria_asociado_a_admin(db_session, tenant):
    rol = Rol(nombre="ADMIN", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo="mensajeria:usar")
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
async def test_permiso_mensajeria_asociado_a_alumno(db_session, tenant):
    rol = Rol(nombre="ALUMNO", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo="mensajeria:usar")
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


def test_audit_codes_perfil_mensajeria_existen():
    from app.core.audit_codes import AuditAction
    assert AuditAction.PERFIL_EDITAR == "PERFIL_EDITAR"
    assert AuditAction.MENSAJE_ENVIAR == "MENSAJE_ENVIAR"
