import uuid
from datetime import date, datetime, timezone

import pytest

from app.models.evaluacion import Evaluacion
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.models.usuario import Usuario
from app.models.auth_user import AuthUser
from app.models.reserva_evaluacion import ReservaEvaluacion
from app.models.resultado_evaluacion import ResultadoEvaluacion
from app.repositories.evaluacion_repository import EvaluacionRepository


@pytest.fixture
async def materia(db_session, tenant):
    m = Materia(tenant_id=tenant.id, codigo=f"REPO-{uuid.uuid4().hex[:6]}", nombre="Repo Materia", estado="Activa")
    db_session.add(m)
    await db_session.flush()
    return m


@pytest.fixture
async def carrera(db_session, tenant):
    c = Carrera(tenant_id=tenant.id, codigo=f"REPO-{uuid.uuid4().hex[:6]}", nombre="Repo Carrera", estado="Activa")
    db_session.add(c)
    await db_session.flush()
    return c


@pytest.fixture
async def cohorte(db_session, tenant, carrera):
    c = Cohorte(tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026-R", anio=2026, vig_desde=date(2026, 1, 1), estado="Activa")
    db_session.add(c)
    await db_session.flush()
    return c


@pytest.fixture
async def alumno_factory(db_session, tenant):
    async def _make(nombre="Alumno", apellidos="Test", legajo=None, email=None):
        idx = str(uuid.uuid4())[:8]
        auth = AuthUser(tenant_id=tenant.id, email=email or f"repo+{idx}@test.com", password_hash="hashed")
        db_session.add(auth)
        await db_session.flush()
        u = Usuario(id=auth.id, tenant_id=tenant.id, nombre=nombre, apellidos=apellidos, legajo=legajo or f"L{idx}")
        db_session.add(u)
        await db_session.flush()
        return u
    return _make


@pytest.fixture
def repo(db_session, tenant):
    return EvaluacionRepository(db_session, tenant.id)


async def test_create_evaluacion(db_session, tenant, materia, cohorte, repo):
    evaluacion = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="Repo test",
        cupos_por_dia=[{"fecha": "2026-06-15", "cupo": 5}],
        alumnos_convocados=[],
    )
    created = await repo.create(evaluacion)
    assert created.id is not None
    assert created.tenant_id == tenant.id
    assert created.materia_id == materia.id


async def test_get_evaluacion(db_session, materia, cohorte, repo):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Parcial",
        instancia="Get test",
        cupos_por_dia=[{"fecha": "2026-06-15", "cupo": 5}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    found = await repo.get(evaluacion.id)
    assert found is not None
    assert found.id == evaluacion.id


async def test_get_evaluacion_not_found(db_session, repo):
    found = await repo.get(uuid.uuid4())
    assert found is None


async def test_list_evaluaciones(db_session, materia, cohorte, repo):
    for i in range(3):
        e = Evaluacion(
            tenant_id=repo._tenant_id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo="TP",
            instancia=f"List test {i}",
            cupos_por_dia=[{"fecha": f"2026-06-{15+i}", "cupo": 5}],
            alumnos_convocados=[],
        )
        await repo.create(e)

    items = await repo.list()
    assert len(items) == 3


async def test_list_with_metrics_includes_counts(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="Metrics test",
        cupos_por_dia=[{"fecha": "2026-06-20", "cupo": 10}],
        alumnos_convocados=[str(uuid.uuid4()), str(uuid.uuid4())],
    )
    await repo.create(evaluacion)

    alumno = await alumno_factory()
    reserva = ReservaEvaluacion(
        tenant_id=repo._tenant_id,
        evaluacion_id=evaluacion.id,
        alumno_id=alumno.id,
        fecha_hora=datetime(2026, 6, 20, 14, 0, tzinfo=timezone.utc),
        estado="Activa",
    )
    db_session.add(reserva)
    await db_session.flush()

    items = await repo.list_with_metrics()
    assert len(items) == 1
    item = items[0]
    assert item["id"] == evaluacion.id
    assert item["total_convocados"] == 2
    assert item["total_reservas"] == 1


async def test_count_reservas_activas_by_date(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="Count test",
        cupos_por_dia=[{"fecha": "2026-07-01", "cupo": 10}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    alumno = await alumno_factory()
    r = ReservaEvaluacion(
        tenant_id=repo._tenant_id,
        evaluacion_id=evaluacion.id,
        alumno_id=alumno.id,
        fecha_hora=datetime(2026, 7, 1, 14, 0, tzinfo=timezone.utc),
        estado="Activa",
    )
    db_session.add(r)
    await db_session.flush()

    count = await repo.count_reservas_activas(evaluacion.id, date(2026, 7, 1))
    assert count == 1


async def test_count_reservas_activas_excludes_canceladas(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="TP",
        instancia="Exclude test",
        cupos_por_dia=[{"fecha": "2026-07-05", "cupo": 5}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    alumno = await alumno_factory()
    r = ReservaEvaluacion(
        tenant_id=repo._tenant_id,
        evaluacion_id=evaluacion.id,
        alumno_id=alumno.id,
        fecha_hora=datetime(2026, 7, 5, 10, 0, tzinfo=timezone.utc),
        estado="Cancelada",
    )
    db_session.add(r)
    await db_session.flush()

    count = await repo.count_reservas_activas(evaluacion.id, date(2026, 7, 5))
    assert count == 0


async def test_get_reserva_activa_found(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="Active test",
        cupos_por_dia=[{"fecha": "2026-08-01", "cupo": 10}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    alumno = await alumno_factory()
    r = ReservaEvaluacion(
        tenant_id=repo._tenant_id,
        evaluacion_id=evaluacion.id,
        alumno_id=alumno.id,
        fecha_hora=datetime(2026, 8, 1, 14, 0, tzinfo=timezone.utc),
        estado="Activa",
    )
    db_session.add(r)
    await db_session.flush()

    found = await repo.get_reserva_activa(evaluacion.id, alumno.id)
    assert found is not None
    assert found.estado == "Activa"


async def test_get_reserva_activa_none(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="TP",
        instancia="None test",
        cupos_por_dia=[{"fecha": "2026-08-15", "cupo": 5}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    found = await repo.get_reserva_activa(evaluacion.id, uuid.uuid4())
    assert found is None


async def test_create_reserva_creates_with_estado_activa(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Parcial",
        instancia="Create reserva test",
        cupos_por_dia=[{"fecha": "2026-09-01", "cupo": 10}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    alumno = await alumno_factory()
    reserva = await repo.create_reserva({
        "evaluacion_id": evaluacion.id,
        "alumno_id": alumno.id,
        "fecha_hora": datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc),
    })
    assert reserva.id is not None
    assert reserva.estado == "Activa"
    assert reserva.evaluacion_id == evaluacion.id
    assert reserva.alumno_id == alumno.id


async def test_get_reserva(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="Get reserva",
        cupos_por_dia=[{"fecha": "2026-10-01", "cupo": 5}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    alumno = await alumno_factory()
    r = ReservaEvaluacion(
        tenant_id=repo._tenant_id,
        evaluacion_id=evaluacion.id,
        alumno_id=alumno.id,
        fecha_hora=datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc),
        estado="Activa",
    )
    db_session.add(r)
    await db_session.flush()

    found = await repo.get_reserva(r.id)
    assert found is not None
    assert found.id == r.id


async def test_list_reservas(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="List reservas",
        cupos_por_dia=[{"fecha": "2026-11-01", "cupo": 10}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    alumno1 = await alumno_factory(nombre="A1", legajo="L1")
    alumno2 = await alumno_factory(nombre="A2", legajo="L2")
    for a, h in [(alumno1, 10), (alumno2, 11)]:
        db_session.add(ReservaEvaluacion(
            tenant_id=repo._tenant_id,
            evaluacion_id=evaluacion.id,
            alumno_id=a.id,
            fecha_hora=datetime(2026, 11, 1, h, 0, tzinfo=timezone.utc),
            estado="Activa",
        ))
    await db_session.flush()

    items = await repo.list_reservas(evaluacion.id)
    assert len(items) == 2


async def test_list_reservas_global_filters_by_tenant(db_session, tenant, tenant_a, materia, cohorte, repo, alumno_factory):
    ev_t = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="Global",
        cupos_por_dia=[{"fecha": "2026-12-01", "cupo": 5}],
        alumnos_convocados=[],
    )
    db_session.add(ev_t)
    await db_session.flush()

    alumno = await alumno_factory()
    db_session.add(ReservaEvaluacion(
        tenant_id=tenant.id,
        evaluacion_id=ev_t.id,
        alumno_id=alumno.id,
        fecha_hora=datetime(2026, 12, 1, 14, 0, tzinfo=timezone.utc),
        estado="Activa",
    ))
    await db_session.flush()

    repo_t = EvaluacionRepository(db_session, tenant.id)
    items_t, total_t = await repo_t.list_reservas_global()
    assert len(items_t) == 1

    repo_a = EvaluacionRepository(db_session, tenant_a.id)
    items_a, total_a = await repo_a.list_reservas_global()
    assert len(items_a) == 0


async def test_create_resultado(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="Resultado test",
        cupos_por_dia=[{"fecha": "2026-12-10", "cupo": 5}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    alumno = await alumno_factory()
    res = await repo.create_resultado({
        "evaluacion_id": evaluacion.id,
        "alumno_id": alumno.id,
        "nota_final": "7.5",
    })
    assert res.id is not None
    assert res.nota_final == "7.5"


async def test_get_resultado(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="TP",
        instancia="Get result",
        cupos_por_dia=[{"fecha": "2026-12-15", "cupo": 10}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    alumno = await alumno_factory()
    r = ResultadoEvaluacion(
        tenant_id=repo._tenant_id,
        evaluacion_id=evaluacion.id,
        alumno_id=alumno.id,
        nota_final="9.0",
    )
    db_session.add(r)
    await db_session.flush()

    found = await repo.get_resultado(evaluacion.id, alumno.id)
    assert found is not None
    assert found.nota_final == "9.0"


async def test_upsert_resultado_inserts(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Recuperatorio",
        instancia="Upsert insert",
        cupos_por_dia=[{"fecha": "2026-12-20", "cupo": 5}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    alumno = await alumno_factory()
    res = await repo.upsert_resultado({
        "evaluacion_id": evaluacion.id,
        "alumno_id": alumno.id,
        "nota_final": "6.0",
    })
    assert res.nota_final == "6.0"


async def test_upsert_resultado_updates(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="Upsert update",
        cupos_por_dia=[{"fecha": "2026-12-25", "cupo": 5}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    alumno = await alumno_factory()
    await repo.create_resultado({
        "evaluacion_id": evaluacion.id,
        "alumno_id": alumno.id,
        "nota_final": "4.0",
    })

    res = await repo.upsert_resultado({
        "evaluacion_id": evaluacion.id,
        "alumno_id": alumno.id,
        "nota_final": "8.5",
    })
    assert res.nota_final == "8.5"


async def test_list_resultados(db_session, materia, cohorte, repo, alumno_factory):
    evaluacion = Evaluacion(
        tenant_id=repo._tenant_id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="List results",
        cupos_por_dia=[{"fecha": "2027-01-01", "cupo": 10}],
        alumnos_convocados=[],
    )
    await repo.create(evaluacion)

    a1 = await alumno_factory(nombre="R1", legajo="LR1")
    a2 = await alumno_factory(nombre="R2", legajo="LR2")
    for a, nota in [(a1, "7.0"), (a2, "8.0")]:
        db_session.add(ResultadoEvaluacion(
            tenant_id=repo._tenant_id,
            evaluacion_id=evaluacion.id,
            alumno_id=a.id,
            nota_final=nota,
        ))
    await db_session.flush()

    items = await repo.list_resultados(evaluacion.id)
    assert len(items) == 2


async def test_list_resultados_global_filters_by_tenant(db_session, tenant, tenant_a, materia, cohorte, repo, alumno_factory):
    ev = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Coloquio",
        instancia="Global result",
        cupos_por_dia=[{"fecha": "2027-02-01", "cupo": 5}],
        alumnos_convocados=[],
    )
    db_session.add(ev)
    await db_session.flush()

    alumno = await alumno_factory()
    db_session.add(ResultadoEvaluacion(
        tenant_id=tenant.id,
        evaluacion_id=ev.id,
        alumno_id=alumno.id,
        nota_final="5.0",
    ))
    await db_session.flush()

    repo_t = EvaluacionRepository(db_session, tenant.id)
    items_t, total_t = await repo_t.list_resultados_global()
    assert len(items_t) == 1

    repo_a = EvaluacionRepository(db_session, tenant_a.id)
    items_a, total_a = await repo_a.list_resultados_global()
    assert len(items_a) == 0


async def test_tenant_isolation_evaluacion(db_session, tenant, tenant_a, materia, cohorte, repo):
    ev = Evaluacion(
        tenant_id=tenant.id,
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="TP",
        instancia="Isolation",
        cupos_por_dia=[{"fecha": "2027-03-01", "cupo": 5}],
        alumnos_convocados=[],
    )
    await repo.create(ev)

    repo_a = EvaluacionRepository(db_session, tenant_a.id)
    found = await repo_a.get(ev.id)
    assert found is None
