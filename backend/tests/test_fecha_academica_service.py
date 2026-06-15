import uuid
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.repositories.fecha_academica_repository import FechaAcademicaRepository
from app.schemas.fechas_academicas import FechaAcademicaCreateRequest, FechaAcademicaUpdateRequest


async def _seed_fas_estructura(db_session: AsyncSession, tenant_id: uuid.UUID):
    suffix = uuid.uuid4().hex[:8]
    c = Carrera(id=uuid.uuid4(), codigo=f"FAS-{suffix}", nombre="Test Carrera", tenant_id=tenant_id)
    db_session.add(c)
    m = Materia(id=uuid.uuid4(), codigo=f"MAT-FAS-{suffix}", nombre="Materia FAS", tenant_id=tenant_id)
    db_session.add(m)
    co = Cohorte(
        id=uuid.uuid4(), carrera_id=c.id, nombre=f"COH-FAS-{suffix}",
        anio=2026, vig_desde=date(2026, 1, 1), tenant_id=tenant_id,
    )
    db_session.add(co)
    await db_session.commit()
    await db_session.refresh(c)
    await db_session.refresh(m)
    await db_session.refresh(co)
    return c, m, co


@pytest.mark.asyncio
async def test_create_fecha_academica(db_session: AsyncSession, tenant):
    from app.services.fecha_academica_service import FechaAcademicaService

    carrera, materia, cohorte = await _seed_fas_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)
    svc = FechaAcademicaService(db_session, repo)

    req = FechaAcademicaCreateRequest(
        materia_id=materia.id,
        cohorte_id=cohorte.id,
        tipo="Parcial",
        numero=1,
        periodo="2026-1",
        fecha=date(2026, 4, 15),
        titulo="Primer Parcial",
    )

    result = await svc.crear(req, tenant.id, uuid.uuid4())
    assert result is not None
    assert result.tipo == "Parcial"
    assert result.numero == 1
    assert result.periodo == "2026-1"
    assert result.fecha == date(2026, 4, 15)
    assert result.titulo == "Primer Parcial"
    assert result.materia_id == materia.id
    assert result.cohorte_id == cohorte.id


@pytest.mark.asyncio
async def test_create_invalid_materia_404(db_session: AsyncSession, tenant):
    from app.services.fecha_academica_service import FechaAcademicaService

    carrera, materia, cohorte = await _seed_fas_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)
    svc = FechaAcademicaService(db_session, repo)

    req = FechaAcademicaCreateRequest(
        materia_id=uuid.uuid4(),
        cohorte_id=cohorte.id,
        tipo="Parcial",
        numero=1,
        periodo="2026-1",
        fecha=date(2026, 4, 15),
    )

    with pytest.raises(HTTPException) as exc:
        await svc.crear(req, tenant.id, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_invalid_cohorte_404(db_session: AsyncSession, tenant):
    from app.services.fecha_academica_service import FechaAcademicaService

    carrera, materia, cohorte = await _seed_fas_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)
    svc = FechaAcademicaService(db_session, repo)

    req = FechaAcademicaCreateRequest(
        materia_id=materia.id,
        cohorte_id=uuid.uuid4(),
        tipo="Parcial",
        numero=1,
        periodo="2026-1",
        fecha=date(2026, 4, 15),
    )

    with pytest.raises(HTTPException) as exc:
        await svc.crear(req, tenant.id, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_by_periodo(db_session: AsyncSession, tenant):
    from app.services.fecha_academica_service import FechaAcademicaService

    carrera, materia, cohorte = await _seed_fas_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)
    svc = FechaAcademicaService(db_session, repo)

    await svc.crear(FechaAcademicaCreateRequest(
        materia_id=materia.id, cohorte_id=cohorte.id,
        tipo="Parcial", numero=1, periodo="2026-1", fecha=date(2026, 4, 15),
    ), tenant.id, uuid.uuid4())
    await svc.crear(FechaAcademicaCreateRequest(
        materia_id=materia.id, cohorte_id=cohorte.id,
        tipo="Parcial", numero=1, periodo="2026-2", fecha=date(2026, 9, 15),
    ), tenant.id, uuid.uuid4())

    items, total = await svc.listar(
        materia_id=None, cohorte_id=None, tipo=None, periodo="2026-1",
        offset=0, limit=10, tenant_id=tenant.id,
    )
    assert total == 1
    assert items[0].periodo == "2026-1"


@pytest.mark.asyncio
async def test_calendario_date_range(db_session: AsyncSession, tenant):
    from app.services.fecha_academica_service import FechaAcademicaService

    carrera, materia, cohorte = await _seed_fas_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)
    svc = FechaAcademicaService(db_session, repo)

    await svc.crear(FechaAcademicaCreateRequest(
        materia_id=materia.id, cohorte_id=cohorte.id,
        tipo="Parcial", numero=1, periodo="2026-1", fecha=date(2026, 4, 15),
    ), tenant.id, uuid.uuid4())
    await svc.crear(FechaAcademicaCreateRequest(
        materia_id=materia.id, cohorte_id=cohorte.id,
        tipo="Parcial", numero=2, periodo="2026-1", fecha=date(2026, 5, 20),
    ), tenant.id, uuid.uuid4())

    items = await svc.calendario(
        tenant_id=tenant.id, fecha_desde=date(2026, 5, 1), fecha_hasta=date(2026, 6, 30),
    )
    assert len(items) == 1
    assert items[0].fecha == date(2026, 5, 20)


@pytest.mark.asyncio
async def test_calendario_ordered(db_session: AsyncSession, tenant):
    from app.services.fecha_academica_service import FechaAcademicaService

    carrera, materia, cohorte = await _seed_fas_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)
    svc = FechaAcademicaService(db_session, repo)

    await svc.crear(FechaAcademicaCreateRequest(
        materia_id=materia.id, cohorte_id=cohorte.id,
        tipo="Coloquio", numero=1, periodo="2026-1", fecha=date(2026, 6, 30),
    ), tenant.id, uuid.uuid4())
    await svc.crear(FechaAcademicaCreateRequest(
        materia_id=materia.id, cohorte_id=cohorte.id,
        tipo="Parcial", numero=1, periodo="2026-1", fecha=date(2026, 4, 15),
    ), tenant.id, uuid.uuid4())

    items = await svc.calendario(tenant_id=tenant.id)
    assert items[0].fecha == date(2026, 4, 15)
    assert items[1].fecha == date(2026, 6, 30)


@pytest.mark.asyncio
async def test_update_partial(db_session: AsyncSession, tenant):
    from app.services.fecha_academica_service import FechaAcademicaService

    carrera, materia, cohorte = await _seed_fas_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)
    svc = FechaAcademicaService(db_session, repo)

    created = await svc.crear(FechaAcademicaCreateRequest(
        materia_id=materia.id, cohorte_id=cohorte.id,
        tipo="Parcial", numero=1, periodo="2026-1", fecha=date(2026, 4, 15),
        titulo="Original",
    ), tenant.id, uuid.uuid4())

    req = FechaAcademicaUpdateRequest(titulo="Actualizado", fecha=date(2026, 4, 20))
    updated = await svc.actualizar(created.id, req, tenant.id, uuid.uuid4())
    assert updated.titulo == "Actualizado"
    assert updated.fecha == date(2026, 4, 20)
    assert updated.tipo == "Parcial"
    assert updated.numero == 1


@pytest.mark.asyncio
async def test_update_not_found_404(db_session: AsyncSession, tenant):
    from app.services.fecha_academica_service import FechaAcademicaService

    repo = FechaAcademicaRepository(db_session, tenant.id)
    svc = FechaAcademicaService(db_session, repo)

    req = FechaAcademicaUpdateRequest(titulo="X")
    with pytest.raises(HTTPException) as exc:
        await svc.actualizar(uuid.uuid4(), req, tenant.id, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_soft_delete_fa(db_session: AsyncSession, tenant):
    from app.services.fecha_academica_service import FechaAcademicaService

    carrera, materia, cohorte = await _seed_fas_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)
    svc = FechaAcademicaService(db_session, repo)

    created = await svc.crear(FechaAcademicaCreateRequest(
        materia_id=materia.id, cohorte_id=cohorte.id,
        tipo="TP", numero=1, periodo="2026-1", fecha=date(2026, 5, 10),
    ), tenant.id, uuid.uuid4())

    await svc.eliminar(created.id, tenant.id, uuid.uuid4())

    with pytest.raises(HTTPException) as exc:
        await svc.actualizar(created.id, FechaAcademicaUpdateRequest(), tenant.id, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_generar_html_lms_with_fechas(db_session: AsyncSession, tenant):
    from app.services.fecha_academica_service import FechaAcademicaService

    carrera, materia, cohorte = await _seed_fas_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)
    svc = FechaAcademicaService(db_session, repo)

    await svc.crear(FechaAcademicaCreateRequest(
        materia_id=materia.id, cohorte_id=cohorte.id,
        tipo="Parcial", numero=1, periodo="2026-1", fecha=date(2026, 4, 15),
        titulo="Primer Parcial",
    ), tenant.id, uuid.uuid4())
    await svc.crear(FechaAcademicaCreateRequest(
        materia_id=materia.id, cohorte_id=cohorte.id,
        tipo="TP", numero=1, periodo="2026-1", fecha=date(2026, 5, 10),
        titulo="TP Integrador",
    ), tenant.id, uuid.uuid4())

    html = await svc.generar_html_lms(materia.id, cohorte.id, tenant.id)
    assert "<table" in html
    assert "Primer Parcial" in html
    assert "TP Integrador" in html
    assert materia.nombre in html
    assert "<link" not in html


@pytest.mark.asyncio
async def test_generar_html_lms_empty(db_session: AsyncSession, tenant):
    from app.services.fecha_academica_service import FechaAcademicaService

    carrera, materia, cohorte = await _seed_fas_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)
    svc = FechaAcademicaService(db_session, repo)

    html = await svc.generar_html_lms(materia.id, cohorte.id, tenant.id)
    assert materia.nombre in html
    assert "no hay fechas" in html.lower()


@pytest.mark.asyncio
async def test_generar_html_lms_materia_not_found(db_session: AsyncSession, tenant):
    from app.services.fecha_academica_service import FechaAcademicaService

    repo = FechaAcademicaRepository(db_session, tenant.id)
    svc = FechaAcademicaService(db_session, repo)

    with pytest.raises(HTTPException) as exc:
        await svc.generar_html_lms(uuid.uuid4(), uuid.uuid4(), tenant.id)
    assert exc.value.status_code == 404
