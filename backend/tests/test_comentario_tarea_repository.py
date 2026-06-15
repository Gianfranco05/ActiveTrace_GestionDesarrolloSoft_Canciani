import uuid

import pytest

from app.models.auth_user import AuthUser
from app.models.comentario_tarea import ComentarioTarea
from app.models.tarea import Tarea
from app.models.usuario import Usuario
from app.repositories.comentario_tarea_repository import ComentarioTareaRepository


async def _crear_usuario(db_session, tenant, nombre="Test", apellidos="User", email=None):
    uid = str(uuid.uuid4())[:8]
    auth = AuthUser(tenant_id=tenant.id, email=email or f"crepo+{uid}@test.com", password_hash="hashed")
    db_session.add(auth)
    await db_session.flush()
    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre=nombre, apellidos=apellidos)
    db_session.add(u)
    await db_session.flush()
    return u


async def _crear_tarea(db_session, tenant, asignado_a, asignado_por):
    tarea = Tarea(tenant_id=tenant.id, asignado_a=asignado_a, asignado_por=asignado_por, descripcion="Tarea comment test")
    db_session.add(tarea)
    await db_session.flush()
    return tarea


@pytest.fixture
def comentario_repo(db_session, tenant):
    return ComentarioTareaRepository(db_session, tenant.id)


@pytest.mark.asyncio
async def test_create_comentario_returns_comentario_with_id(db_session, tenant, comentario_repo):
    u1 = await _crear_usuario(db_session, tenant, "Autor")
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = await _crear_tarea(db_session, tenant, u1.id, u2.id)

    comentario = ComentarioTarea(
        tenant_id=tenant.id,
        tarea_id=tarea.id,
        autor_id=u1.id,
        texto="Primer comentario de prueba",
    )
    created = await comentario_repo.create(comentario)
    assert created.id is not None
    assert created.texto == "Primer comentario de prueba"


@pytest.mark.asyncio
async def test_list_by_tarea_returns_ordered(db_session, tenant, comentario_repo):
    u1 = await _crear_usuario(db_session, tenant, "Autor")
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = await _crear_tarea(db_session, tenant, u1.id, u2.id)

    c1 = ComentarioTarea(tenant_id=tenant.id, tarea_id=tarea.id, autor_id=u1.id, texto="Primero")
    c2 = ComentarioTarea(tenant_id=tenant.id, tarea_id=tarea.id, autor_id=u1.id, texto="Segundo")
    await comentario_repo.create(c1)
    await comentario_repo.create(c2)

    items = await comentario_repo.list_by_tarea(tarea.id, tenant.id)
    assert len(items) == 2
    assert items[0].creado_at <= items[1].creado_at


@pytest.mark.asyncio
async def test_list_by_tarea_tenant_isolation(db_session, tenant, tenant_b, comentario_repo):
    u1 = await _crear_usuario(db_session, tenant, "Autor")
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = await _crear_tarea(db_session, tenant, u1.id, u2.id)

    c = ComentarioTarea(tenant_id=tenant.id, tarea_id=tarea.id, autor_id=u1.id, texto="Test")
    await comentario_repo.create(c)

    repo_b = ComentarioTareaRepository(db_session, tenant_b.id)
    items_b = await repo_b.list_by_tarea(tarea.id, tenant_b.id)
    assert len(items_b) == 0


@pytest.mark.asyncio
async def test_list_empty_tarea(db_session, tenant, comentario_repo):
    items = await comentario_repo.list_by_tarea(uuid.uuid4(), tenant.id)
    assert len(items) == 0


@pytest.mark.asyncio
async def test_comentario_autor_nombre_resolved(db_session, tenant, comentario_repo):
    u1 = await _crear_usuario(db_session, tenant, "Juan", "Pérez")
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = await _crear_tarea(db_session, tenant, u1.id, u2.id)

    c = ComentarioTarea(tenant_id=tenant.id, tarea_id=tarea.id, autor_id=u1.id, texto="Con autor")
    await comentario_repo.create(c)

    items = await comentario_repo.list_by_tarea(tarea.id, tenant.id)
    assert len(items) == 1
    assert items[0].autor.nombre == "Juan"
    assert items[0].autor.apellidos == "Pérez"
