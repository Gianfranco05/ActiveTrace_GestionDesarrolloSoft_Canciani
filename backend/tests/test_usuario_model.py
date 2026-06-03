
import uuid

import pytest

from app.models.auth_user import AuthUser
from app.models.usuario import Usuario


async def test_create_usuario(db_session, tenant):
    # create via UsuarioService so PII is encrypted
    from app.services.usuario_service import UsuarioService
    svc = UsuarioService(db_session, tenant.id)
    data = {"nombre": "Juan", "apellidos": "Perez", "dni": "12345678", "cuil": "20-12345678-3", "cbu": "0123456789012345678901", "alias_cbu": "juan.alias"}
    u = await svc.create(data)
    assert u.id is not None
    assert u.tenant_id == tenant.id
    assert u.nombre == "Juan"
    assert u.apellidos == "Perez"
    # PII stored encrypted by service
    assert u.dni != "12345678"
    assert u.cuil != "20-12345678-3"
    assert u.cbu != "0123456789012345678901"
    assert u.alias_cbu != "juan.alias"
    assert u.facturador is False
    assert u.estado == "Activo"
    assert u.created_at is not None


async def test_usuario_1to1_fk_enforced(db_session, tenant):
    nonexistent_id = uuid.uuid4()
    u = Usuario(
        id=nonexistent_id,
        tenant_id=tenant.id,
        nombre="FK",
        apellidos="Test",
    )
    db_session.add(u)
    import sqlalchemy.exc
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_usuario_default_facturador_false(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="fact@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)

    u = Usuario(
        id=auth.id,
        tenant_id=tenant.id,
        nombre="Def",
        apellidos="Fact",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    assert u.facturador is False


async def test_usuario_default_estado_activo(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="estado@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)

    u = Usuario(
        id=auth.id,
        tenant_id=tenant.id,
        nombre="Def",
        apellidos="Est",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    assert u.estado == "Activo"


async def test_usuario_soft_delete(db_session, tenant):
    from app.repositories.usuario_repository import UsuarioRepository
    repo = UsuarioRepository(db_session, tenant.id)
    data = {"nombre": "Soft", "apellidos": "Del", "dni": "999"}
    u = await repo.create(data)
    assert u.deleted_at is None

    deleted = await repo.soft_delete(u.id)
    assert deleted is True

    fetched = await repo.get(u.id)
    assert fetched is None

    lst = await repo.list()
    ids = [i.id for i in lst]
    assert u.id not in ids
