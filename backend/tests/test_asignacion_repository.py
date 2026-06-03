from app.repositories.asignacion_repository import AsignacionRepository
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.tenant import Tenant
from datetime import date, timedelta


async def create_sample_usuario(session, tenant):
    u = Usuario(tenant_id=tenant.id, nombre="RepoU", apellidos="X")
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


async def create_sample_rol(session, tenant):
    r = Rol(tenant_id=tenant.id, nombre="R")
    session.add(r)
    await session.commit()
    await session.refresh(r)
    return r


async def test_create_asignacion_repo(db_session, tenant):
    usuario = await create_sample_usuario(db_session, tenant)
    rol = await create_sample_rol(db_session, tenant)
    repo = AsignacionRepository(db_session, tenant.id)
    data = {"usuario_id": usuario.id, "rol_id": rol.id, "vig_desde": date.today()}
    a = await repo.create(data)
    assert a.id is not None
    lst = await repo.get_by_usuario(usuario.id)
    assert len(lst) >= 1


async def test_get_by_usuario_empty(db_session, tenant):
    repo = AsignacionRepository(db_session, tenant.id)
    usuario = await create_sample_usuario(db_session, tenant)
    lst = await repo.get_by_usuario(usuario.id)
    assert lst == []


async def test_get_activas_by_usuario_excludes_expired(db_session, tenant):
    usuario = await create_sample_usuario(db_session, tenant)
    rol = await create_sample_rol(db_session, tenant)
    repo = AsignacionRepository(db_session, tenant.id)

    await repo.create({
        "usuario_id": usuario.id,
        "rol_id": rol.id,
        "vig_desde": date.today() - timedelta(days=30),
        "vig_hasta": date.today() - timedelta(days=1),
    })

    activas = await repo.get_activas_by_usuario(usuario.id)
    assert len(activas) == 0


async def test_get_activas_by_usuario_includes_open_ended(db_session, tenant):
    usuario = await create_sample_usuario(db_session, tenant)
    rol = await create_sample_rol(db_session, tenant)
    repo = AsignacionRepository(db_session, tenant.id)

    a = await repo.create({
        "usuario_id": usuario.id,
        "rol_id": rol.id,
        "vig_desde": date.today() - timedelta(days=10),
    })

    activas = await repo.get_activas_by_usuario(usuario.id)
    assert len(activas) >= 1
    assert activas[0].id == a.id


async def test_tenant_isolation(db_session, tenant):
    tenant2 = Tenant(name="T2-AsigRepo", slug="t2-asigrepo")
    db_session.add(tenant2)
    await db_session.commit()
    await db_session.refresh(tenant2)

    repo1 = AsignacionRepository(db_session, tenant.id)
    repo2 = AsignacionRepository(db_session, tenant2.id)

    u1 = await create_sample_usuario(db_session, tenant)
    r1 = await create_sample_rol(db_session, tenant)

    u2 = Usuario(tenant_id=tenant2.id, nombre="U2", apellidos="T2")
    db_session.add(u2)
    await db_session.commit()
    await db_session.refresh(u2)
    r2 = Rol(tenant_id=tenant2.id, nombre="R2")
    db_session.add(r2)
    await db_session.commit()
    await db_session.refresh(r2)

    await repo1.create({"usuario_id": u1.id, "rol_id": r1.id, "vig_desde": date.today()})
    await repo2.create({"usuario_id": u2.id, "rol_id": r2.id, "vig_desde": date.today()})

    lst1 = await repo1.list()
    lst2 = await repo2.list()
    for a in lst1:
        assert a.tenant_id == tenant.id
    for a in lst2:
        assert a.tenant_id == tenant2.id
