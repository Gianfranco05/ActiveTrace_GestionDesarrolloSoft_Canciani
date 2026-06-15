import uuid

import pytest
from sqlalchemy import select

from app.models.auth_user import AuthUser
from app.models.comentario_tarea import ComentarioTarea
from app.models.materia import Materia
from app.models.tarea import Tarea
from app.models.usuario import Usuario


async def _crear_usuario(db_session, tenant, nombre="Test", apellidos="User", email=None):
    uid = str(uuid.uuid4())[:8]
    auth = AuthUser(tenant_id=tenant.id, email=email or f"model+{uid}@test.com", password_hash="hashed")
    db_session.add(auth)
    await db_session.flush()
    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre=nombre, apellidos=apellidos)
    db_session.add(u)
    await db_session.flush()
    return u


async def _crear_materia(db_session, tenant, codigo=None):
    m = Materia(tenant_id=tenant.id, codigo=codigo or f"M-{str(uuid.uuid4())[:6]}", nombre="Materia Test")
    db_session.add(m)
    await db_session.flush()
    return m


@pytest.mark.asyncio
async def test_tarea_creation(db_session, tenant):
    u1 = await _crear_usuario(db_session, tenant, "Docente", "Asignado")
    u2 = await _crear_usuario(db_session, tenant, "Coordinador", "Asignante")
    m = await _crear_materia(db_session, tenant)

    tarea = Tarea(
        tenant_id=tenant.id,
        materia_id=m.id,
        asignado_a=u1.id,
        asignado_por=u2.id,
        descripcion="Revisar notas de la cohorte",
    )
    db_session.add(tarea)
    await db_session.commit()
    await db_session.refresh(tarea)

    assert tarea.id is not None
    assert tarea.tenant_id == tenant.id
    assert tarea.materia_id == m.id
    assert tarea.asignado_a == u1.id
    assert tarea.asignado_por == u2.id
    assert tarea.descripcion == "Revisar notas de la cohorte"
    assert tarea.estado == "Pendiente"


@pytest.mark.asyncio
async def test_tarea_estado_default(db_session, tenant):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")

    tarea = Tarea(
        tenant_id=tenant.id,
        asignado_a=u1.id,
        asignado_por=u2.id,
        descripcion="Tarea de prueba",
    )
    db_session.add(tarea)
    await db_session.commit()
    await db_session.refresh(tarea)
    assert tarea.estado == "Pendiente"


@pytest.mark.asyncio
async def test_tarea_materia_nullable(db_session, tenant):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")

    tarea = Tarea(
        tenant_id=tenant.id,
        asignado_a=u1.id,
        asignado_por=u2.id,
        descripcion="Tarea institucional",
        materia_id=None,
    )
    db_session.add(tarea)
    await db_session.commit()
    await db_session.refresh(tarea)
    assert tarea.materia_id is None


@pytest.mark.asyncio
async def test_tarea_contexto_nullable(db_session, tenant):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")

    tarea = Tarea(
        tenant_id=tenant.id,
        asignado_a=u1.id,
        asignado_por=u2.id,
        descripcion="Tarea sin contexto",
    )
    db_session.add(tarea)
    await db_session.commit()
    await db_session.refresh(tarea)
    assert tarea.contexto_id is None


@pytest.mark.asyncio
async def test_comentario_creation(db_session, tenant):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="Tarea")
    db_session.add(tarea)
    await db_session.commit()
    await db_session.refresh(tarea)

    comentario = ComentarioTarea(
        tenant_id=tenant.id,
        tarea_id=tarea.id,
        autor_id=u1.id,
        texto="Comentario de prueba",
    )
    db_session.add(comentario)
    await db_session.commit()
    await db_session.refresh(comentario)

    assert comentario.id is not None
    assert comentario.tarea_id == tarea.id
    assert comentario.autor_id == u1.id
    assert comentario.texto == "Comentario de prueba"


@pytest.mark.asyncio
async def test_comentario_creado_at_auto(db_session, tenant):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="T")
    db_session.add(tarea)
    await db_session.commit()
    await db_session.refresh(tarea)

    comentario = ComentarioTarea(
        tenant_id=tenant.id,
        tarea_id=tarea.id,
        autor_id=u1.id,
        texto="Test",
    )
    db_session.add(comentario)
    await db_session.commit()
    await db_session.refresh(comentario)
    assert comentario.creado_at is not None


@pytest.mark.asyncio
async def test_soft_delete_tarea(db_session, tenant):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="Tarea")
    db_session.add(tarea)
    await db_session.commit()
    await db_session.refresh(tarea)

    from datetime import datetime, timezone
    tarea.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    result = await db_session.execute(
        select(Tarea).where(Tarea.id == tarea.id, Tarea.deleted_at.isnot(None)),
    )
    assert result.scalar_one_or_none() is not None

    result_active = await db_session.execute(
        select(Tarea).where(Tarea.id == tarea.id, Tarea.deleted_at.is_(None)),
    )
    assert result_active.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_tenant_id_not_null(db_session, tenant):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")

    with pytest.raises(Exception):
        tarea = Tarea(
            tenant_id=None,
            asignado_a=u1.id,
            asignado_por=u2.id,
            descripcion="Falla",
        )
        db_session.add(tarea)
        await db_session.flush()


@pytest.mark.asyncio
async def test_tarea_asignado_por_fk(db_session, tenant):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="FK test")
    db_session.add(tarea)
    await db_session.commit()
    await db_session.refresh(tarea)

    result = await db_session.execute(
        select(Usuario).where(Usuario.id == tarea.asignado_por),
    )
    user = result.scalar_one()
    assert user.id == u2.id


@pytest.mark.asyncio
async def test_comentario_tarea_relacion(db_session, tenant):
    u1 = await _crear_usuario(db_session, tenant)
    u2 = await _crear_usuario(db_session, tenant, "Coord")
    tarea = Tarea(tenant_id=tenant.id, asignado_a=u1.id, asignado_por=u2.id, descripcion="Relacion")
    db_session.add(tarea)
    await db_session.commit()
    await db_session.refresh(tarea)

    c = ComentarioTarea(tenant_id=tenant.id, tarea_id=tarea.id, autor_id=u1.id, texto="Rel")
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    await db_session.refresh(tarea, ["comentarios"])

    assert len(tarea.comentarios) == 1
    assert tarea.comentarios[0].id == c.id
