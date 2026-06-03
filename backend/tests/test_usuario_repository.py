

from app.repositories.usuario_repository import UsuarioRepository
from app.models.tenant import Tenant


async def test_create_usuario_repo(db_session, tenant):
    repo = UsuarioRepository(db_session, tenant.id)
    data = {"nombre": "Repo", "apellidos": "Test", "dni": "555"}
    u = await repo.create(data)
    assert u.id is not None
    fetched = await repo.get(u.id)
    assert fetched is not None
    assert fetched.nombre == "Repo"


async def test_get_by_legajo_found(db_session, tenant):
    repo = UsuarioRepository(db_session, tenant.id)
    data = {"nombre": "Leg", "apellidos": "Test", "legajo": "L-001"}
    u = await repo.create(data)
    fetched = await repo.get_by_legajo("L-001")
    assert fetched is not None
    assert fetched.id == u.id
    assert fetched.nombre == "Leg"


async def test_get_by_legajo_not_found(db_session, tenant):
    repo = UsuarioRepository(db_session, tenant.id)
    result = await repo.get_by_legajo("NONEXISTENT")
    assert result is None


async def test_list_excludes_soft_deleted(db_session, tenant):
    repo = UsuarioRepository(db_session, tenant.id)
    u1 = await repo.create({"nombre": "Keep", "apellidos": "Me"})
    u2 = await repo.create({"nombre": "Delete", "apellidos": "Me"})

    lst = await repo.list()
    assert len(lst) >= 2

    await repo.soft_delete(u2.id)
    lst2 = await repo.list()
    ids = [i.id for i in lst2]
    assert u1.id in ids
    assert u2.id not in ids


async def test_tenant_isolation(db_session, tenant):
    tenant2 = Tenant(name="tenant2", slug="tenant2")
    db_session.add(tenant2)
    await db_session.commit()
    await db_session.refresh(tenant2)

    repo1 = UsuarioRepository(db_session, tenant.id)
    repo2 = UsuarioRepository(db_session, tenant2.id)

    await repo1.create({"nombre": "T1", "apellidos": "User"})
    await repo2.create({"nombre": "T2", "apellidos": "User"})

    lst1 = await repo1.list()
    lst2 = await repo2.list()
    assert len(lst1) >= 1
    assert len(lst2) >= 1
    for u in lst1:
        assert u.tenant_id == tenant.id
    for u in lst2:
        assert u.tenant_id == tenant2.id
