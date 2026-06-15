"""TDD: AsignacionRepository equipo operations — RED → GREEN → TRIANGULATE."""

import uuid
from datetime import date

import pytest

from app.models.asignacion import Asignacion
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.repositories.asignacion_repository import AsignacionRepository


async def _create_usuario(session, tenant, nombre="RepoEquipo"):
    u = Usuario(tenant_id=tenant.id, nombre=nombre, apellidos="Test")
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


async def _create_rol(session, tenant, nombre="PROFESOR"):
    r = Rol(tenant_id=tenant.id, nombre=nombre)
    session.add(r)
    await session.commit()
    await session.refresh(r)
    return r


async def _create_materia(session, tenant, cod="MAT-EQ"):
    m = Materia(codigo=cod, nombre="Test Materia", tenant_id=tenant.id)
    session.add(m)
    await session.commit()
    await session.refresh(m)
    return m


async def _create_carrera(session, tenant, cod="CAR-EQ"):
    c = Carrera(codigo=cod, nombre="Test Carrera", tenant_id=tenant.id)
    session.add(c)
    await session.commit()
    await session.refresh(c)
    return c


async def _create_cohorte(session, tenant, carrera, nombre="COH-EQ"):
    c = Cohorte(carrera_id=carrera.id, nombre=nombre, anio=2026, vig_desde=date.today(), tenant_id=tenant.id)
    session.add(c)
    await session.commit()
    await session.refresh(c)
    return c


async def _create_asignacion(session, tenant, usuario_id, rol_id, **kwargs):
    a = Asignacion(
        tenant_id=tenant.id,
        usuario_id=usuario_id,
        rol_id=rol_id,
        vig_desde=kwargs.get("vig_desde", date.today()),
        vig_hasta=kwargs.get("vig_hasta"),
        materia_id=kwargs.get("materia_id"),
        carrera_id=kwargs.get("carrera_id"),
        cohorte_id=kwargs.get("cohorte_id"),
        comisiones=kwargs.get("comisiones"),
    )
    session.add(a)
    await session.commit()
    await session.refresh(a)
    return a


@pytest.mark.asyncio
async def test_get_equipo_returns_asignaciones(db_session, tenant):
    """RED 1.1: get_equipo returns all Asignaciones for a (materia, carrera, cohorte)."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    a1 = await _create_asignacion(db_session, tenant, u.id, r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id)
    a2 = await _create_asignacion(db_session, tenant, u.id, r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id)

    repo = AsignacionRepository(db_session, tenant.id)
    result = await repo.get_equipo(mat.id, car.id, coh.id)

    assert len(result) == 2
    assert {a.id for a in result} == {a1.id, a2.id}


@pytest.mark.asyncio
async def test_get_equipo_empty_returns_empty_list(db_session, tenant):
    """TRIANGULATE: empty equipo returns empty list."""
    repo = AsignacionRepository(db_session, tenant.id)
    result = await repo.get_equipo(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    assert result == []


@pytest.mark.asyncio
async def test_get_equipos_agrupados_returns_grouped(db_session, tenant):
    """get_equipos_agrupados returns distinct (materia, carrera, cohorte) groups with counts."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)
    mat1 = await _create_materia(db_session, tenant, cod="MAT-EQ1")
    car1 = await _create_carrera(db_session, tenant, cod="CAR-EQ1")
    coh1 = await _create_cohorte(db_session, tenant, car1, nombre="COH-EQ1")
    mat2 = await _create_materia(db_session, tenant, cod="MAT-EQ2")
    car2 = await _create_carrera(db_session, tenant, cod="CAR-EQ2")
    coh2 = await _create_cohorte(db_session, tenant, car2, nombre="COH-EQ2")

    await _create_asignacion(db_session, tenant, u.id, r.id, materia_id=mat1.id, carrera_id=car1.id, cohorte_id=coh1.id)
    await _create_asignacion(db_session, tenant, u.id, r.id, materia_id=mat1.id, carrera_id=car1.id, cohorte_id=coh1.id)
    await _create_asignacion(db_session, tenant, u.id, r.id, materia_id=mat2.id, carrera_id=car2.id, cohorte_id=coh2.id)

    repo = AsignacionRepository(db_session, tenant.id)
    groups = await repo.get_equipos_agrupados(tenant.id)

    assert len(groups) == 2
    group_map = {(g.materia_id, g.carrera_id, g.cohorte_id): g.count for g in groups}
    assert group_map[(mat1.id, car1.id, coh1.id)] == 2
    assert group_map[(mat2.id, car2.id, coh2.id)] == 1


@pytest.mark.asyncio
async def test_bulk_create_creates_all(db_session, tenant):
    """TRIANGULATE: bulk_create creates all asignaciones."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)
    mat = await _create_materia(db_session, tenant)

    asignaciones = [
        Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, vig_desde=date.today()),
        Asignacion(tenant_id=tenant.id, usuario_id=u.id, rol_id=r.id, materia_id=mat.id, vig_desde=date.today()),
    ]
    repo = AsignacionRepository(db_session, tenant.id)
    created = await repo.bulk_create(asignaciones)

    assert len(created) == 2
    assert all(a.id is not None for a in created)
    assert all(a.materia_id == mat.id for a in created)


@pytest.mark.asyncio
async def test_update_vigencia_batch_updates_all(db_session, tenant):
    """TRIANGULATE: update_vigencia_batch updates all matching asignaciones."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    await _create_asignacion(db_session, tenant, u.id, r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id)
    await _create_asignacion(db_session, tenant, u.id, r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id)

    repo = AsignacionRepository(db_session, tenant.id)
    new_vig = date(2025, 1, 1)
    updated = await repo.update_vigencia_batch((mat.id, car.id, coh.id), new_vig, None)

    assert updated == 2

    result = await repo.get_equipo(mat.id, car.id, coh.id)
    assert all(a.vig_desde == new_vig for a in result)
    assert all(a.vig_hasta is None for a in result)


@pytest.mark.asyncio
async def test_get_equipo_with_relations_returns_joined_data(db_session, tenant):
    """get_equipo_with_relations returns dicts with joined relations."""
    u = await _create_usuario(db_session, tenant)
    r = await _create_rol(db_session, tenant)
    mat = await _create_materia(db_session, tenant)
    car = await _create_carrera(db_session, tenant)
    coh = await _create_cohorte(db_session, tenant, car)

    await _create_asignacion(db_session, tenant, u.id, r.id, materia_id=mat.id, carrera_id=car.id, cohorte_id=coh.id)

    repo = AsignacionRepository(db_session, tenant.id)
    rows = await repo.get_equipo_with_relations(mat.id, car.id, coh.id)

    assert len(rows) == 1
    assert rows[0]["usuario"].id == u.id
    assert rows[0]["rol"].id == r.id


@pytest.mark.asyncio
async def test_search_usuarios_by_name(db_session, tenant):
    """TRIANGULATE: search_usuarios finds by nombre."""
    u = Usuario(tenant_id=tenant.id, nombre="Martín", apellidos="García")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    repo = AsignacionRepository(db_session, tenant.id)
    results = await repo.search_usuarios("Martín", tenant.id)

    assert len(results) >= 1
    assert results[0].id == u.id


@pytest.mark.asyncio
async def test_search_usuarios_by_legajo(db_session, tenant):
    """TRIANGULATE: search_usuarios finds by legajo."""
    u = Usuario(tenant_id=tenant.id, nombre="Laura", apellidos="Pérez", legajo="LEG-001")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    repo = AsignacionRepository(db_session, tenant.id)
    results = await repo.search_usuarios("LEG-001", tenant.id)

    assert len(results) == 1
    assert results[0].id == u.id


@pytest.mark.asyncio
async def test_tenant_isolation_on_search(db_session, tenant):
    """TRIANGULATE: search only returns users from same tenant."""
    from app.models.tenant import Tenant
    other = Tenant(name="Other-Repo", slug="other-repo")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    u1 = Usuario(tenant_id=tenant.id, nombre="Juan", apellidos="Pérez")
    u2 = Usuario(tenant_id=other.id, nombre="Juan", apellidos="Pérez")
    db_session.add_all([u1, u2])
    await db_session.commit()

    repo = AsignacionRepository(db_session, tenant.id)
    results = await repo.search_usuarios("Juan", tenant.id)

    assert len(results) == 1
    assert results[0].tenant_id == tenant.id
