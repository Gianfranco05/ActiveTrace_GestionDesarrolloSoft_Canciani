import uuid
from datetime import date

import pytest
import sqlalchemy as sa

from app.models.evaluacion import Evaluacion
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.models.usuario import Usuario
from app.models.auth_user import AuthUser
from app.models.resultado_evaluacion import ResultadoEvaluacion


@pytest.fixture
async def materia(db_session, tenant):
    m = Materia(
        tenant_id=tenant.id,
        codigo="MAT-301",
        nombre="Quimica I",
        estado="Activa",
    )
    db_session.add(m)
    await db_session.flush()
    return m


@pytest.fixture
async def carrera(db_session, tenant):
    c = Carrera(
        tenant_id=tenant.id,
        codigo="QMC",
        nombre="Quimica",
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
        nombre="2026-C",
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
        email="alumno301@test.com",
        password_hash="hashed",
    )
    db_session.add(auth)
    await db_session.flush()
    u = Usuario(
        id=auth.id,
        tenant_id=tenant.id,
        nombre="Alumno",
        apellidos="TresCeroUno",
        legajo="AL301",
    )
    db_session.add(u)
    await db_session.flush()
    return u


async def test_resultado_creation(db_session, tenant, materia, cohorte, alumno):
    evaluacion = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="Final 2026",
        cupos_por_dia=[{"fecha": "2026-12-01", "cupo": 10}],
        alumnos_convocados=[],
    )
    db_session.add(evaluacion)
    await db_session.flush()

    resultado = ResultadoEvaluacion(
        tenant_id=tenant.id,
        evaluacion_id=evaluacion.id,
        alumno_id=alumno.id,
        nota_final="8.5",
    )
    db_session.add(resultado)
    await db_session.flush()

    assert resultado.id is not None
    assert resultado.tenant_id == tenant.id
    assert resultado.evaluacion_id == evaluacion.id
    assert resultado.alumno_id == alumno.id
    assert resultado.nota_final == "8.5"
    assert resultado.created_at is not None


async def test_resultado_unique_constraint(db_session, tenant, materia, cohorte, alumno):
    evaluacion = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Recuperatorio",
        instancia="Recuperatorio final",
        cupos_por_dia=[{"fecha": "2026-12-15", "cupo": 5}],
        alumnos_convocados=[],
    )
    db_session.add(evaluacion)
    await db_session.flush()

    r1 = ResultadoEvaluacion(
        tenant_id=tenant.id,
        evaluacion_id=evaluacion.id,
        alumno_id=alumno.id,
        nota_final="7.0",
    )
    db_session.add(r1)
    await db_session.flush()

    r2 = ResultadoEvaluacion(
        tenant_id=tenant.id,
        evaluacion_id=evaluacion.id,
        alumno_id=alumno.id,
        nota_final="9.0",
    )
    db_session.add(r2)
    with pytest.raises(Exception):
        await db_session.flush()
