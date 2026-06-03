import uuid
from datetime import date, timedelta

import pytest
import sqlalchemy.exc

from app.models.asignacion import Asignacion
from app.models.usuario import Usuario
from app.models.rol import Rol


async def create_sample_usuario(session, tenant):
    u = Usuario(
        tenant_id=tenant.id,
        nombre="Ana",
        apellidos="Gomez",
        dni="11111111",
    )
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


async def create_sample_rol(session, tenant):
    r = Rol(tenant_id=tenant.id, nombre="Profesor")
    session.add(r)
    await session.commit()
    await session.refresh(r)
    return r


async def test_create_asignacion(db_session, tenant):
    usuario = await create_sample_usuario(db_session, tenant)
    rol = await create_sample_rol(db_session, tenant)
    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date.today() - timedelta(days=1),
    )
    db_session.add(a)
    await db_session.commit()
    assert a.id is not None
    assert a.usuario_id == usuario.id
    assert a.rol_id == rol.id


async def test_estado_vigencia_vigente(db_session, tenant):
    usuario = await create_sample_usuario(db_session, tenant)
    rol = await create_sample_rol(db_session, tenant)
    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date.today() - timedelta(days=1),
        vig_hasta=date.today() + timedelta(days=1),
    )
    assert a.estado_vigencia == "Vigente"


async def test_estado_vigencia_vencida(db_session, tenant):
    usuario = await create_sample_usuario(db_session, tenant)
    rol = await create_sample_rol(db_session, tenant)
    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date.today() - timedelta(days=10),
        vig_hasta=date.today() - timedelta(days=1),
    )
    assert a.estado_vigencia == "Vencida"


async def test_asignacion_fk_usuario_enforced(db_session, tenant):
    rol = await create_sample_rol(db_session, tenant)
    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=uuid.uuid4(),
        rol_id=rol.id,
        vig_desde=date.today(),
    )
    db_session.add(a)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_asignacion_fk_rol_enforced(db_session, tenant):
    usuario = await create_sample_usuario(db_session, tenant)
    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=uuid.uuid4(),
        vig_desde=date.today(),
    )
    db_session.add(a)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_asignacion_nullable_context(db_session, tenant):
    usuario = await create_sample_usuario(db_session, tenant)
    rol = await create_sample_rol(db_session, tenant)
    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date.today(),
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)
    assert a.materia_id is None
    assert a.carrera_id is None
    assert a.cohorte_id is None



async def test_asignacion_self_referential_fk(db_session, tenant):
    usuario = await create_sample_usuario(db_session, tenant)
    rol = await create_sample_rol(db_session, tenant)
    a1 = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        vig_desde=date.today(),
    )
    db_session.add(a1)
    await db_session.commit()
    await db_session.refresh(a1)

    a2 = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario.id,
        rol_id=rol.id,
        responsable_id=a1.id,
        vig_desde=date.today(),
    )
    db_session.add(a2)
    await db_session.commit()
    await db_session.refresh(a2)
    assert a2.responsable_id == a1.id


async def test_asignacion_soft_delete(db_session, tenant):
    from app.repositories.asignacion_repository import AsignacionRepository
    usuario = await create_sample_usuario(db_session, tenant)
    rol = await create_sample_rol(db_session, tenant)
    repo = AsignacionRepository(db_session, tenant.id)
    data = {"usuario_id": usuario.id, "rol_id": rol.id, "vig_desde": date.today()}
    a = await repo.create(data)
    assert a.deleted_at is None

    deleted = await repo.soft_delete(a.id)
    assert deleted is True

    fetched = await repo.get(a.id)
    assert fetched is None

    lst = await repo.list()
    ids = [i.id for i in lst]
    assert a.id not in ids
