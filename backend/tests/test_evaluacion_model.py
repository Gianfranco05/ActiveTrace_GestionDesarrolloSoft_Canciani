import uuid
from datetime import date

import pytest
from sqlalchemy import select

from app.models.evaluacion import Evaluacion
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera


@pytest.fixture
async def materia(db_session, tenant):
    m = Materia(
        tenant_id=tenant.id,
        codigo="MAT-101",
        nombre="Matematica I",
        estado="Activa",
    )
    db_session.add(m)
    await db_session.flush()
    return m


@pytest.fixture
async def carrera(db_session, tenant):
    c = Carrera(
        tenant_id=tenant.id,
        codigo="ING",
        nombre="Ingenieria",
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
        nombre="2026-A",
        anio=2026,
        vig_desde=date(2026, 1, 1),
        estado="Activa",
    )
    db_session.add(c)
    await db_session.flush()
    return c


@pytest.mark.parametrize("tipo", ["Parcial", "TP", "Coloquio", "Recuperatorio"])
async def test_evaluacion_creation(tipo, db_session, tenant, materia, cohorte):
    evaluacion = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo=tipo,
        instancia="Primer cuatrimestre 2026",
        cupos_por_dia=[
            {"fecha": "2026-06-15", "cupo": 5},
            {"fecha": "2026-06-16", "cupo": 3},
        ],
        alumnos_convocados=[],
    )
    db_session.add(evaluacion)
    await db_session.flush()

    assert evaluacion.id is not None
    assert evaluacion.tenant_id == tenant.id
    assert evaluacion.materia_id == materia.id
    assert evaluacion.cohorte_id == cohorte.id
    assert evaluacion.tipo == tipo
    assert evaluacion.instancia == "Primer cuatrimestre 2026"
    assert len(evaluacion.cupos_por_dia) == 2
    assert evaluacion.activa is True
    assert evaluacion.alumnos_convocados == []
    assert evaluacion.created_at is not None
    assert evaluacion.updated_at is not None


async def test_evaluacion_cupos_por_dia_jsonb_roundtrip(db_session, tenant, materia, cohorte):
    cupos = [
        {"fecha": "2026-07-01", "cupo": 10},
        {"fecha": "2026-07-02", "cupo": 15},
    ]
    evaluacion = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="Julio 2026",
        cupos_por_dia=cupos,
        alumnos_convocados=[],
    )
    db_session.add(evaluacion)
    await db_session.flush()
    await db_session.refresh(evaluacion)

    assert evaluacion.cupos_por_dia == cupos
    assert evaluacion.cupos_por_dia[0]["fecha"] == "2026-07-01"
    assert evaluacion.cupos_por_dia[0]["cupo"] == 10


async def test_evaluacion_alumnos_convocados_jsonb_roundtrip(db_session, tenant, materia, cohorte):
    alumno_ids = [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]
    evaluacion = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Parcial",
        instancia="Parcial 1",
        cupos_por_dia=[{"fecha": "2026-08-01", "cupo": 20}],
        alumnos_convocados=alumno_ids,
    )
    db_session.add(evaluacion)
    await db_session.flush()
    await db_session.refresh(evaluacion)

    assert len(evaluacion.alumnos_convocados) == 3
    assert evaluacion.alumnos_convocados[0] in alumno_ids


async def test_evaluacion_activa_default_true(db_session, tenant, materia, cohorte):
    evaluacion = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="TP",
        instancia="TP integrador",
        cupos_por_dia=[{"fecha": "2026-09-01", "cupo": 25}],
        alumnos_convocados=[],
    )
    db_session.add(evaluacion)
    await db_session.flush()

    assert evaluacion.activa is True


async def test_evaluacion_set_activa_false(db_session, tenant, materia, cohorte):
    evaluacion = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Recuperatorio",
        instancia="Recuperatorio 1",
        cupos_por_dia=[{"fecha": "2026-10-01", "cupo": 5}],
        alumnos_convocados=[],
        activa=False,
    )
    db_session.add(evaluacion)
    await db_session.flush()

    assert evaluacion.activa is False
