import pytest
from sqlalchemy import select

from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso


@pytest.mark.asyncio
async def test_permiso_perfil_editar_exists(db_session, tenant):
    p = Permiso(codigo="perfil:editar")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    result = await db_session.execute(
        select(Permiso).where(Permiso.codigo == "perfil:editar"),
    )
    permiso = result.scalar_one()
    assert permiso.codigo == "perfil:editar"
    assert permiso.id is not None


@pytest.mark.asyncio
async def test_permiso_perfil_asociado_a_profesor(db_session, tenant):
    rol = Rol(nombre="PROFESOR", tenant_id=tenant.id)
    db_session.add(rol)
    p = Permiso(codigo="perfil:editar")
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
