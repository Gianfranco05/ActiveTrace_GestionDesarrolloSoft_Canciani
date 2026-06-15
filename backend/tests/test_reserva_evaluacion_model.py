import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select

from app.models.evaluacion import Evaluacion
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.models.usuario import Usuario
from app.models.auth_user import AuthUser
from app.models.reserva_evaluacion import ReservaEvaluacion


@pytest.fixture
async def materia(db_session, tenant):
    m = Materia(
        tenant_id=tenant.id,
        codigo="MAT-201",
        nombre="Fisica I",
        estado="Activa",
    )
    db_session.add(m)
    await db_session.flush()
    return m


@pytest.fixture
async def carrera(db_session, tenant):
    c = Carrera(
        tenant_id=tenant.id,
        codigo="FIS",
        nombre="Fisica",
        estado="Activa",
    )
    db_session.add(c)
    await db_session.flush()
    return c


@pytest.fixture
async def cohorte(db_session, tenant, carrera):
    c = Cohorte(
        tenant_id=tenant.id,
        carrera_id=carrera.id,
        nombre="2026-B",
        anio=2026,
        vig_desde=date(2026, 1, 1),
        estado="Activa",
    )
    db_session.add(c)
    await db_session.flush()
    return c


@pytest.fixture
async def alumno(db_session, tenant):
    auth = AuthUser(
        tenant_id=tenant.id,
        email="alumno@test.com",
        password_hash="hashed",
    )
    db_session.add(auth)
    await db_session.flush()
    u = Usuario(
        id=auth.id,
        tenant_id=tenant.id,
        nombre="Alumno",
        apellidos="Test",
        legajo="AL001",
    )
    db_session.add(u)
    await db_session.flush()
    return u


async def test_reserva_creation(db_session, tenant, materia, cohorte, alumno):
    evaluacion = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="Coloquio final",
        cupos_por_dia=[{"fecha": "2026-06-20", "cupo": 10}],
        alumnos_convocados=[],
    )
    db_session.add(evaluacion)
    await db_session.flush()

    reserva = ReservaEvaluacion(
        tenant_id=tenant.id,
        evaluacion_id=evaluacion.id,
        alumno_id=alumno.id,
        fecha_hora=datetime(2026, 6, 20, 14, 0, tzinfo=timezone.utc),
    )
    db_session.add(reserva)
    await db_session.flush()

    assert reserva.id is not None
    assert reserva.tenant_id == tenant.id
    assert reserva.evaluacion_id == evaluacion.id
    assert reserva.alumno_id == alumno.id
    assert reserva.fecha_hora is not None
    assert reserva.estado == "Activa"
    assert reserva.created_at is not None


async def test_reserva_estado_default_activa(db_session, tenant, materia, cohorte, alumno):
    evaluacion = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="TP",
        instancia="TP final",
        cupos_por_dia=[{"fecha": "2026-06-21", "cupo": 8}],
        alumnos_convocados=[],
    )
    db_session.add(evaluacion)
    await db_session.flush()

    reserva = ReservaEvaluacion(
        tenant_id=tenant.id,
        evaluacion_id=evaluacion.id,
        alumno_id=alumno.id,
        fecha_hora=datetime(2026, 6, 21, 10, 0, tzinfo=timezone.utc),
    )
    db_session.add(reserva)
    await db_session.flush()

    assert reserva.estado == "Activa"


async def test_reserva_estados_validos(db_session, tenant, materia, cohorte, alumno):
    evaluacion = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Parcial",
        instancia="Parcial 2",
        cupos_por_dia=[{"fecha": "2026-06-22", "cupo": 12}],
        alumnos_convocados=[],
    )
    db_session.add(evaluacion)
    await db_session.flush()

    reserva1 = ReservaEvaluacion(
        tenant_id=tenant.id,
        evaluacion_id=evaluacion.id,
        alumno_id=alumno.id,
        fecha_hora=datetime(2026, 6, 22, 10, 0, tzinfo=timezone.utc),
        estado="Activa",
    )
    db_session.add(reserva1)
    await db_session.flush()
    assert reserva1.estado == "Activa"

    alumno2 = AuthUser(
        tenant_id=tenant.id,
        email="alumno2@test.com",
        password_hash="hashed",
    )
    db_session.add(alumno2)
    await db_session.flush()
    u2 = Usuario(
        id=alumno2.id,
        tenant_id=tenant.id,
        nombre="Alumno",
        apellidos="Dos",
        legajo="AL002",
    )
    db_session.add(u2)
    await db_session.flush()

    reserva2 = ReservaEvaluacion(
        tenant_id=tenant.id,
        evaluacion_id=evaluacion.id,
        alumno_id=u2.id,
        fecha_hora=datetime(2026, 6, 22, 11, 0, tzinfo=timezone.utc),
        estado="Cancelada",
    )
    db_session.add(reserva2)
    await db_session.flush()
    assert reserva2.estado == "Cancelada"
