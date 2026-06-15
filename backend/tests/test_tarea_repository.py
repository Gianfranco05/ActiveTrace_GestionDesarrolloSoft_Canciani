import uuid

import pytest

from app.models.auth_user import AuthUser
from app.models.materia import Materia
from app.models.tarea import Tarea
from app.models.usuario import Usuario
from app.repositories.tarea_repository import TareaRepository


async def _crear_usuario(db_session, tenant, nombre="Test", apellidos="User", email=None):
    uid = str(uuid.uuid4())[:8]
    auth = AuthUser(tenant_id=tenant.id, email=email or f"repo+{uid}@test.com", password_hash="hashed")
    db_session.add(auth)
    await db_session.flush()
    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre=nombre, apellidos=apellidos)
    db_session.add(u)
    await db_session.flush()
    return u


async def _crear_materia(db_session, tenant, codigo=None):
    m = Materia(tenant_id=tenant.id, codigo=codigo or f"REPO-{str(uuid.uuid4())[:6]}", nombre="Repo Materia")
    db_session.add(m)
    await db_session.flush()
    return m


@pytest.fixture
def tarea_repo(db_session, tenant):
    return TareaRepository(db_session, tenant.id)


@pytest.mark.asyncio
async def test_create_tarea_returns_tarea_with_id(db_session, tenant, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant, "Docente", "Asignado")
    u2 = await _crear_usuario(db_session, tenant, "Coord", "Asignante")

    tarea = Tarea(
        tenant_id=tenant.id,
        asignado_a=u1.id,
        asignado_por=u2.id,
        descripcion="Repo create test",
    )
    created = await tarea_repo.create(tarea)
    assert created.id is not None
    assert created.estado == "Pendiente"


@pytest.mark.asyncio
async def test_get_by_id_returns_tarea(db_session, tenant, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="Get test")
    await tarea_repo.create(tarea)

    found = await tarea_repo.get_by_id(tarea.id, tenant.id)
    assert found is not None
    assert found.id == tarea.id


@pytest.mark.asyncio
async def test_get_by_id_tenant_isolation(db_session, tenant, tenant_b, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="Tenant isolation")
    await tarea_repo.create(tarea)

    repo_b = TareaRepository(db_session, tenant_b.id)
    found = await repo_b.get_by_id(tarea.id, tenant_b.id)
    assert found is None


@pytest.mark.asyncio
async def test_get_by_id_returns_404(db_session, tenant, tarea_repo):
    found = await tarea_repo.get_by_id(uuid.uuid4(), tenant.id)
    assert found is None


@pytest.mark.asyncio
async def test_update_partial_fields(db_session, tenant, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="Original")
    await tarea_repo.create(tarea)

    updated = await tarea_repo.update(tarea.id, tenant.id, descripcion="Actualizada")
    assert updated is not None
    assert updated.descripcion == "Actualizada"


@pytest.mark.asyncio
async def test_list_by_estado_filter(db_session, tenant, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")

    t1 = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="A", estado="Pendiente")
    t2 = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="B", estado="En progreso")
    await tarea_repo.create(t1)
    await tarea_repo.create(t2)

    items, total = await tarea_repo.list_by_filters(tenant.id, estado="Pendiente")
    assert total == 1
    assert items[0].estado == "Pendiente"


@pytest.mark.asyncio
async def test_list_by_materia_filter(db_session, tenant, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    m1 = await _crear_materia(db_session, tenant)

    tarea = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="Con materia", materia_id=m1.id)
    tarea2 = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="Sin materia", materia_id=None)
    await tarea_repo.create(tarea)
    await tarea_repo.create(tarea2)

    items, total = await tarea_repo.list_by_filters(tenant.id, materia_id=m1.id)
    assert total == 1
    assert items[0].materia_id == m1.id


@pytest.mark.asyncio
async def test_list_by_asignado_a_filter(db_session, tenant, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant, "Docente1")
    u2 = await _crear_usuario(db_session, tenant, "Docente2")
    u_coord = await _crear_usuario(db_session, tenant, "Coord")

    await tarea_repo.create(Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u_coord.id, descripcion="U1"))
    await tarea_repo.create(Tarea(tenant_id=tenant.id, asignado_a=u2.id, asignado_por=u_coord.id, descripcion="U2"))

    items, total = await tarea_repo.list_by_filters(tenant.id, asignado_a=u1.id)
    assert total == 1


@pytest.mark.asyncio
async def test_list_by_asignado_por_filter(db_session, tenant, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord1")
    u3 = await _crear_usuario(db_session, tenant, "Coord2")

    await tarea_repo.create(Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="C1"))
    await tarea_repo.create(Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u3.id, descripcion="C2"))

    items, total = await tarea_repo.list_by_filters(tenant.id, asignado_por=u2.id)
    assert total == 1


@pytest.mark.asyncio
async def test_list_fulltext_search_q(db_session, tenant, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")

    await tarea_repo.create(Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="Revisar seguimiento"))
    await tarea_repo.create(Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="Completar planilla"))

    items, total = await tarea_repo.list_by_filters(tenant.id, q="seguimiento")
    assert total == 1
    assert "seguimiento" in items[0].descripcion.lower()


@pytest.mark.asyncio
async def test_list_combined_filters(db_session, tenant, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    m = await _crear_materia(db_session, tenant)

    await tarea_repo.create(Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="Match", estado="Pendiente", materia_id=m.id))
    await tarea_repo.create(Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="No match", estado="En progreso", materia_id=m.id))

    items, total = await tarea_repo.list_by_filters(tenant.id, estado="Pendiente", materia_id=m.id)
    assert total == 1


@pytest.mark.asyncio
async def test_list_pagination(db_session, tenant, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")

    for i in range(5):
        t = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion=f"Tarea {i}")
        await tarea_repo.create(t)

    items, total = await tarea_repo.list_by_filters(tenant.id, offset=0, limit=2)
    assert total == 5
    assert len(items) == 2

    items2, _ = await tarea_repo.list_by_filters(tenant.id, offset=4, limit=2)
    assert len(items2) == 1


@pytest.mark.asyncio
async def test_list_tenant_isolation(db_session, tenant, tenant_b, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    await tarea_repo.create(Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="T-A"))

    repo_b = TareaRepository(db_session, tenant_b.id)
    _, total_b = await repo_b.list_by_filters(tenant_b.id)
    assert total_b == 0


@pytest.mark.asyncio
async def test_get_for_update_locks_row(db_session, tenant, tarea_repo):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="Lock test")
    await tarea_repo.create(tarea)

    locked = await tarea_repo.get_for_update(tarea.id, tenant.id)
    assert locked is not None
    assert locked.id == tarea.id
