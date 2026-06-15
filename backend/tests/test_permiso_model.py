import pytest
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
async def test_create_permiso(db_session):
    from app.models.permiso import Permiso

    permiso = Permiso(
        codigo="calificaciones:importar",
        descripcion="Importar calificaciones",
    )
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(permiso)

    assert permiso.id is not None
    assert permiso.codigo == "calificaciones:importar"
    assert permiso.descripcion == "Importar calificaciones"
    assert permiso.created_at is not None


@pytest.mark.asyncio
async def test_permiso_codigo_unique(db_session):
    from app.models.permiso import Permiso

    p1 = Permiso(codigo="auditoria:ver", descripcion="Auditar")
    db_session.add(p1)
    await db_session.commit()

    p2 = Permiso(codigo="auditoria:ver", descripcion="Duplicate")
    db_session.add(p2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_permiso_no_tenant_scope(db_session):
    from app.models.permiso import Permiso

    permiso = Permiso(codigo="usuarios:gestionar")
    db_session.add(permiso)
    await db_session.commit()
    await db_session.refresh(permiso)

    assert not hasattr(permiso, "tenant_id")
