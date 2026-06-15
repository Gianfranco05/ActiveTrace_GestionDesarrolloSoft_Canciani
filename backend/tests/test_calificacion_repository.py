"""TDD: CalificacionRepository tests."""

import uuid
from datetime import datetime, timezone

import pytest

from app.models.calificacion import Calificacion
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.models.usuario import Usuario
from app.models.auth_user import AuthUser
from app.models.padron import VersionPadron, EntradaPadron
from app.repositories.calificacion_repository import CalificacionRepository


async def _create_prereqs(db_session, tenant) -> dict:
    carrera = Carrera(codigo="REP-CAR", nombre="Test", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    materia = Materia(codigo="REP-MAT", nombre="Test", tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()
    await db_session.refresh(materia)

    cohorte = Cohorte(
        carrera_id=carrera.id, nombre="REP-2026", anio=2026,
        vig_desde=datetime.now(timezone.utc).date(), tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    await db_session.commit()
    await db_session.refresh(cohorte)

    auth_user = AuthUser(tenant_id=tenant.id, email="rep@test.com", password_hash="hash")
    db_session.add(auth_user)
    await db_session.commit()
    await db_session.refresh(auth_user)

    usuario = Usuario(id=auth_user.id, tenant_id=tenant.id, nombre="Rep", apellidos="Test")
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    vp = VersionPadron(tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id)
    db_session.add(vp)
    await db_session.commit()
    await db_session.refresh(vp)

    ep = EntradaPadron(
        tenant_id=tenant.id, version_id=vp.id, nombre="Ana", apellidos="Lopez", email="ana@test.com",
    )
    db_session.add(ep)
    await db_session.commit()
    await db_session.refresh(ep)

    return {
        "materia": materia, "cohorte": cohorte, "usuario": usuario,
        "entrada_padron": ep, "version_padron": vp,
    }


@pytest.mark.asyncio
async def test_bulk_create(db_session, tenant):
    """RED 5.1: bulk_create persists list of Calificacion dicts."""
    prereqs = await _create_prereqs(db_session, tenant)
    repo = CalificacionRepository(db_session, tenant.id)

    califs = [
        {
            "materia_id": prereqs["materia"].id,
            "cohorte_id": prereqs["cohorte"].id,
            "entrada_padron_id": prereqs["entrada_padron"].id,
            "actividad": "TP1",
            "tipo": "Numerica",
            "nota_numerica": 75.00,
            "aprobado": True,
            "origen": "Importado",
            "cargado_por": prereqs["usuario"].id,
        },
        {
            "materia_id": prereqs["materia"].id,
            "cohorte_id": prereqs["cohorte"].id,
            "entrada_padron_id": prereqs["entrada_padron"].id,
            "actividad": "TP2",
            "tipo": "Numerica",
            "nota_numerica": 45.00,
            "aprobado": False,
            "origen": "Importado",
            "cargado_por": prereqs["usuario"].id,
        },
    ]

    created = await repo.bulk_create(califs)
    assert len(created) == 2
    for c in created:
        assert c.id is not None
        assert c.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_get_by_materia_y_cohorte_paginated(db_session, tenant):
    """TRIANGULATE 5.4: get with pagination."""
    prereqs = await _create_prereqs(db_session, tenant)
    repo = CalificacionRepository(db_session, tenant.id)

    # Create 3 calificaciones
    for i in range(3):
        await repo.bulk_create([
            {
                "materia_id": prereqs["materia"].id,
                "cohorte_id": prereqs["cohorte"].id,
                "entrada_padron_id": prereqs["entrada_padron"].id,
                "actividad": f"TP{i}",
                "tipo": "Numerica",
                "nota_numerica": 60.00 + i * 10,
                "aprobado": True,
                "origen": "Importado",
                "cargado_por": prereqs["usuario"].id,
            },
        ])

    items, total = await repo.get_by_materia_y_cohorte(
        prereqs["materia"].id, prereqs["cohorte"].id,
        offset=0, limit=2,
    )
    assert total == 3
    assert len(items) == 2


@pytest.mark.asyncio
async def test_get_by_materia_y_cohorte_filters_by_cargado_por(db_session, tenant):
    """TRIANGULATE 5.4: filter by cargado_por."""
    prereqs = await _create_prereqs(db_session, tenant)
    repo = CalificacionRepository(db_session, tenant.id)

    auth_user2 = AuthUser(tenant_id=tenant.id, email="rep2@test.com", password_hash="hash")
    db_session.add(auth_user2)
    await db_session.commit()
    await db_session.refresh(auth_user2)
    usuario2 = Usuario(id=auth_user2.id, tenant_id=tenant.id, nombre="Rep2", apellidos="Test")
    db_session.add(usuario2)
    await db_session.commit()
    await db_session.refresh(usuario2)

    await repo.bulk_create([
        {
            "materia_id": prereqs["materia"].id, "cohorte_id": prereqs["cohorte"].id,
            "entrada_padron_id": prereqs["entrada_padron"].id,
            "actividad": "TP1", "tipo": "Numerica",
            "nota_numerica": 80, "aprobado": True,
            "origen": "Importado", "cargado_por": prereqs["usuario"].id,
        },
        {
            "materia_id": prereqs["materia"].id, "cohorte_id": prereqs["cohorte"].id,
            "entrada_padron_id": prereqs["entrada_padron"].id,
            "actividad": "TP2", "tipo": "Numerica",
            "nota_numerica": 70, "aprobado": True,
            "origen": "Importado", "cargado_por": usuario2.id,
        },
    ])

    items, total = await repo.get_by_materia_y_cohorte(
        prereqs["materia"].id, prereqs["cohorte"].id,
        cargado_por=prereqs["usuario"].id,
    )
    assert total == 1
    assert items[0].actividad == "TP1"


@pytest.mark.asyncio
async def test_get_by_entrada_padron_found(db_session, tenant):
    """TRIANGULATE 5.4: find by entrada_padron + actividad."""
    prereqs = await _create_prereqs(db_session, tenant)
    repo = CalificacionRepository(db_session, tenant.id)

    await repo.bulk_create([
        {
            "materia_id": prereqs["materia"].id, "cohorte_id": prereqs["cohorte"].id,
            "entrada_padron_id": prereqs["entrada_padron"].id,
            "actividad": "TP1", "tipo": "Numerica",
            "nota_numerica": 80, "aprobado": True,
            "origen": "Importado", "cargado_por": prereqs["usuario"].id,
        },
    ])

    result = await repo.get_by_entrada_padron(prereqs["entrada_padron"].id, "TP1")
    assert result is not None
    assert result.actividad == "TP1"


@pytest.mark.asyncio
async def test_get_by_entrada_padron_not_found(db_session, tenant):
    """TRIANGULATE 5.4: not found returns None."""
    repo = CalificacionRepository(db_session, tenant.id)
    result = await repo.get_by_entrada_padron(uuid.uuid4(), "TP1")
    assert result is None


@pytest.mark.asyncio
async def test_count_by_actividad(db_session, tenant):
    """TRIANGULATE 5.4: count by actividad."""
    prereqs = await _create_prereqs(db_session, tenant)
    repo = CalificacionRepository(db_session, tenant.id)

    await repo.bulk_create([
        {
            "materia_id": prereqs["materia"].id, "cohorte_id": prereqs["cohorte"].id,
            "entrada_padron_id": prereqs["entrada_padron"].id,
            "actividad": "TP1", "tipo": "Numerica",
            "nota_numerica": 80, "aprobado": True,
            "origen": "Importado", "cargado_por": prereqs["usuario"].id,
        },
        {
            "materia_id": prereqs["materia"].id, "cohorte_id": prereqs["cohorte"].id,
            "entrada_padron_id": prereqs["entrada_padron"].id,
            "actividad": "TP1", "tipo": "Numerica",
            "nota_numerica": 60, "aprobado": True,
            "origen": "Importado", "cargado_por": prereqs["usuario"].id,
        },
    ])

    count = await repo.count_by_actividad(prereqs["materia"].id, prereqs["cohorte"].id, "TP1")
    assert count == 2


@pytest.mark.asyncio
async def test_tenant_isolation_repo(db_session, tenant_a, tenant_b):
    """TRIANGULATE 5.4: tenant isolation."""
    pa = await _create_prereqs(db_session, tenant_a)
    pb = await _create_prereqs(db_session, tenant_b)
    repo_a = CalificacionRepository(db_session, tenant_a.id)

    await repo_a.bulk_create([
        {
            "materia_id": pa["materia"].id, "cohorte_id": pa["cohorte"].id,
            "entrada_padron_id": pa["entrada_padron"].id,
            "actividad": "TP1", "tipo": "Numerica",
            "nota_numerica": 80, "aprobado": True,
            "origen": "Importado", "cargado_por": pa["usuario"].id,
        },
    ])

    repo_b = CalificacionRepository(db_session, tenant_b.id)
    await repo_b.bulk_create([
        {
            "materia_id": pb["materia"].id, "cohorte_id": pb["cohorte"].id,
            "entrada_padron_id": pb["entrada_padron"].id,
            "actividad": "TP1", "tipo": "Numerica",
            "nota_numerica": 90, "aprobado": True,
            "origen": "Importado", "cargado_por": pb["usuario"].id,
        },
    ])

    items_a, total_a = await repo_a.get_by_materia_y_cohorte(pa["materia"].id, pa["cohorte"].id)
    assert total_a == 1

    items_b, total_b = await repo_a.get_by_materia_y_cohorte(pb["materia"].id, pb["cohorte"].id)
    assert total_b == 0
