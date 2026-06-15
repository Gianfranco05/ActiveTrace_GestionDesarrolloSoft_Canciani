"""TDD: Model tests for SlotEncuentro, InstanciaEncuentro, Guardia."""

import uuid
from datetime import date, datetime, time, timezone

import pytest

from app.models.slot_encuentro import SlotEncuentro
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.guardia import Guardia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.asignacion import Asignacion


async def _create_asignacion(db_session, tenant):
    """Helper: create a complete chain for Asignacion FK references."""
    suid = uuid.uuid4().hex[:6]
    materia = Materia(codigo=f"TM-{suid}", nombre="Materia Test", tenant_id=tenant.id)
    db_session.add(materia)

    carrera = Carrera(codigo=f"TC-{suid}", nombre="Carrera Test", tenant_id=tenant.id)
    db_session.add(carrera)

    au = AuthUser(
        tenant_id=tenant.id,
        email=f"test_model_{uuid.uuid4().hex[:8]}@t.com",
        password_hash="x",
    )
    db_session.add(au)
    await db_session.flush()

    usuario = Usuario(
        id=au.id, tenant_id=tenant.id, nombre="Test", apellidos="Model",
        legajo=f"MOD-{suid}",
    )
    db_session.add(usuario)

    rol = Rol(nombre=f"PROFESOR-{suid}", tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.flush()

    cohorte = Cohorte(
        carrera_id=carrera.id, nombre=f"C-{suid}", anio=2026,
        vig_desde=date(2026, 1, 1), tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    await db_session.flush()

    asignacion = Asignacion(
        usuario_id=usuario.id,
        rol_id=rol.id,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        tenant_id=tenant.id,
        vig_desde=date(2026, 1, 1),
    )
    db_session.add(asignacion)
    await db_session.commit()
    await db_session.refresh(asignacion)

    return asignacion, materia, carrera, cohorte


@pytest.mark.asyncio
async def test_slot_encuentro_creation(db_session, tenant):
    asignacion, materia, _, _ = await _create_asignacion(db_session, tenant)

    slot = SlotEncuentro(
        tenant_id=tenant.id,
        asignacion_id=asignacion.id,
        materia_id=materia.id,
        titulo="Clase de Matemáticas",
        hora=time(14, 0),
        dia_semana="Lunes",
        fecha_inicio=date(2026, 6, 8),
        cant_semanas=4,
    )
    db_session.add(slot)
    await db_session.commit()
    await db_session.refresh(slot)

    assert slot.id is not None
    assert isinstance(slot.id, uuid.UUID)
    assert slot.titulo == "Clase de Matemáticas"
    assert slot.hora == time(14, 0)
    assert slot.dia_semana == "Lunes"
    assert slot.cant_semanas == 4


@pytest.mark.asyncio
async def test_instancia_encuentro_creation(db_session, tenant):
    asignacion, materia, _, _ = await _create_asignacion(db_session, tenant)

    instancia = InstanciaEncuentro(
        tenant_id=tenant.id,
        materia_id=materia.id,
        asignacion_id=asignacion.id,
        fecha=date(2026, 6, 8),
        hora=time(14, 0),
        titulo="Clase 1",
    )
    db_session.add(instancia)
    await db_session.commit()
    await db_session.refresh(instancia)

    assert instancia.id is not None
    assert isinstance(instancia.id, uuid.UUID)
    assert instancia.titulo == "Clase 1"
    assert instancia.estado == "Programado"
    assert instancia.slot_id is None


@pytest.mark.asyncio
async def test_instancia_slot_nullable(db_session, tenant):
    asignacion, materia, _, _ = await _create_asignacion(db_session, tenant)

    instancia = InstanciaEncuentro(
        tenant_id=tenant.id,
        slot_id=None,
        materia_id=materia.id,
        asignacion_id=asignacion.id,
        fecha=date(2026, 6, 8),
        hora=time(14, 0),
        titulo="Encuentro único",
    )
    db_session.add(instancia)
    await db_session.commit()
    await db_session.refresh(instancia)

    assert instancia.slot_id is None
    assert instancia.estado == "Programado"


@pytest.mark.asyncio
async def test_instancia_estado_default(db_session, tenant):
    asignacion, materia, _, _ = await _create_asignacion(db_session, tenant)

    instancia = InstanciaEncuentro(
        tenant_id=tenant.id,
        materia_id=materia.id,
        asignacion_id=asignacion.id,
        fecha=date(2026, 6, 8),
        hora=time(14, 0),
        titulo="Test",
    )
    db_session.add(instancia)
    await db_session.commit()
    await db_session.refresh(instancia)

    assert instancia.estado == "Programado"


@pytest.mark.asyncio
async def test_guardia_creation(db_session, tenant):
    asignacion, materia, carrera, cohorte = await _create_asignacion(db_session, tenant)

    guardia = Guardia(
        tenant_id=tenant.id,
        asignacion_id=asignacion.id,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        dia="Lunes",
        horario="14:00–14:45",
        comentarios="Consulta sobre TP",
    )
    db_session.add(guardia)
    await db_session.commit()
    await db_session.refresh(guardia)

    assert guardia.id is not None
    assert isinstance(guardia.id, uuid.UUID)
    assert guardia.dia == "Lunes"
    assert guardia.horario == "14:00–14:45"
    assert guardia.comentarios == "Consulta sobre TP"
    assert guardia.creada_at is not None


@pytest.mark.asyncio
async def test_guardia_estado_default(db_session, tenant):
    asignacion, materia, carrera, cohorte = await _create_asignacion(db_session, tenant)

    guardia = Guardia(
        tenant_id=tenant.id,
        asignacion_id=asignacion.id,
        materia_id=materia.id,
        carrera_id=carrera.id,
        cohorte_id=cohorte.id,
        dia="Martes",
        horario="10:00–10:45",
    )
    db_session.add(guardia)
    await db_session.commit()
    await db_session.refresh(guardia)

    assert guardia.estado == "Pendiente"


@pytest.mark.asyncio
async def test_soft_delete_slot(db_session, tenant):
    asignacion, materia, _, _ = await _create_asignacion(db_session, tenant)

    slot = SlotEncuentro(
        tenant_id=tenant.id,
        asignacion_id=asignacion.id,
        materia_id=materia.id,
        titulo="Para borrar",
        hora=time(9, 0),
        dia_semana="Miércoles",
        fecha_inicio=date(2026, 6, 3),
        cant_semanas=2,
    )
    db_session.add(slot)
    await db_session.commit()

    slot.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(slot)

    assert slot.deleted_at is not None


@pytest.mark.asyncio
async def test_tenant_id_not_null(db_session, tenant):
    asignacion, materia, _, _ = await _create_asignacion(db_session, tenant)

    slot = SlotEncuentro(
        tenant_id=tenant.id,
        asignacion_id=asignacion.id,
        materia_id=materia.id,
        titulo="Test",
        hora=time(10, 0),
        dia_semana="Jueves",
        fecha_inicio=date(2026, 6, 4),
        cant_semanas=1,
    )
    db_session.add(slot)
    await db_session.commit()
    await db_session.refresh(slot)

    assert slot.tenant_id == tenant.id
